import uuid
from datetime import datetime
from typing import Union, List, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne, DESCENDING

from jonbot.backend.data_layer.models.conversation_models import MessageHistory, ChatMessage
from jonbot.backend.data_layer.models.database_request_response_models import UpsertDiscordMessagesRequest, \
    ContextMemoryDocumentRequest, MessageHistoryRequest, UpsertDiscordChatsRequest
from jonbot.backend.data_layer.models.discord_stuff.discord_id import DiscordUserID
from jonbot.backend.data_layer.models.discord_stuff.discord_message_document import DiscordMessageDocument
from jonbot.backend.data_layer.models.user_stuff.memory.context_memory_document import ContextMemoryDocument
from jonbot.backend.data_layer.models.user_stuff.user_ids import UserID
from jonbot.system.environment_variables import (
    MONGO_URI,
    USERS_COLLECTION_NAME,
    RAW_MESSAGES_COLLECTION_NAME,
    CONTEXT_MEMORIES_COLLECTION_NAME,
    CHATS_COLLECTION_NAME,
)
from jonbot.system.setup_logging.get_logger import get_jonbot_logger

logger = get_jonbot_logger()


class MongoDatabaseManager:
    def __init__(self):
        logger.info(f"Initializing MongoDatabaseManager...")
        self._client = AsyncIOMotorClient(MONGO_URI)

    def get_database(self, database_name: str):
        return self._client[database_name]

    def get_collection(self, database_name: str, collection_name: str):
        database = self.get_database(database_name)
        return database[collection_name]

    async def upsert_one(self,
                         database_name: str,
                         data: dict,
                         collection_name: str,
                         query: dict
                         ) -> bool:

        collection = self.get_collection(database_name=database_name, collection_name=collection_name)
        try:
            collection.update_one(filter=query, update={"$set": data}, upsert=True)
            return True
        except Exception as e:
            logger.error(f"Error occurred while upserting. Error: {e}")
            return False

    async def upsert_many(
            self,
            database_name: str,
            entries: List[Dict[str, dict]],
            collection_name: str
    ) -> bool:
        operations = [
            UpdateOne(entry["query"], {"$set": entry["data"]}, upsert=True)
            for entry in entries
        ]
        collection = self.get_collection(
            database_name=database_name, collection_name=collection_name
        )
        try:
            await collection.bulk_write(operations)
            return True
        except Exception as e:
            logger.error(f"Error occurred while upserting. Error: {e}")
            return False

    async def get_sorted_documents(
            self,
            database_name: str,
            collection_name: str,
            query: dict,
            sort_field: str = None,
            limit: int = None,
            sort_order: int = DESCENDING,
    ) -> list:
        try:
            collection = self.get_collection(
                database_name=database_name, collection_name=collection_name
            )
            if sort_field is not None:
                cursor = collection.find(query).sort(sort_field, sort_order)
            else:
                cursor = collection.find(query)

            # Apply the limit if specified
            if limit is not None:
                cursor = cursor.limit(limit)

            documents = await cursor.to_list(length=None)
            return documents
        except Exception as e:
            logger.error(
                f"Error occurred while fetching and sorting documents. Error: {e}"
            )
            return []

    async def upsert_discord_chats(
            self, request: UpsertDiscordChatsRequest
    ) -> bool:

        entries = []
        for document, query in zip(request.data, request.query):
            data = document.dict()
            data["last_updated"] = datetime.now()
            entries.append({"data": data, "query": query})

        return await self.upsert_many(
            database_name=request.database_name,
            entries=entries,
            collection_name=CHATS_COLLECTION_NAME,
        )

    async def upsert_discord_messages(
            self, request: UpsertDiscordMessagesRequest
    ) -> bool:

        entries = []
        for document, query in zip(request.data, request.query):
            data = document.dict()
            data["last_updated"] = datetime.now()
            entries.append({"data": data, "query": query})

        return await self.upsert_many(
            database_name=request.database_name,
            entries=entries,
            collection_name=RAW_MESSAGES_COLLECTION_NAME,
        )

    async def upsert_context_memory(
            self, request: ContextMemoryDocumentRequest
    ) -> bool:
        data = request.data.dict()
        data["last_updated"] = datetime.now()
        entries = [{"data": data, "query": request.query}]

        return await self.upsert_many(
            database_name=request.database_name,
            entries=entries,
            collection_name=CONTEXT_MEMORIES_COLLECTION_NAME,
        )

    async def get_message_history(
            self, request: MessageHistoryRequest
    ) -> MessageHistory:
        documents = await self.get_sorted_documents(
            database_name=request.database_name,
            collection_name=RAW_MESSAGES_COLLECTION_NAME,
            query=request.query,
            sort_field="timestamp.unix_timestamp_utc",
            limit=request.limit_messages,
            sort_order=DESCENDING,
        )

        message_history = MessageHistory()
        for document in documents:
            discord_message_document = DiscordMessageDocument(**document)
            chat_message = ChatMessage.from_discord_message_document(
                discord_message_document
            )
            message_history.add_message(chat_message)
        return message_history

    async def get_context_memory(
            self, request: ContextMemoryDocumentRequest
    ) -> Optional[ContextMemoryDocument]:
        messages_collection = self.get_collection(
            request.database_name, CONTEXT_MEMORIES_COLLECTION_NAME
        )
        query = {**request.query}
        result = await messages_collection.find_one(query)

        if result is None:
            logger.warning(f"Context memory not found with query: {query}")
            return None

        return ContextMemoryDocument(**result)

    async def get_or_create_user(
            self,
            database_name: str,
            discord_id: DiscordUserID = None,
    ) -> str:
        user = await self.get_user(
            database_name, discord_id=discord_id
        )
        if user is None:
            logger.debug(f"User not found. Creating new user.")
            user = await self.create_user(
                database_name, discord_id=discord_id
            )
        if user is None:
            logger.error(f"Failed to create user.")
            raise Exception(f"Failed to create user.")
        logger.success(f"User found: {user}")
        return user.uuid

    async def get_user(
            self,
            database_name: str,
            discord_id: DiscordUserID = None,
    ) -> Union[None, UserID]:
        users_collection = self.get_collection(database_name, USERS_COLLECTION_NAME)

        query = {}
        if discord_id is not None:
            query["discord_id"] = discord_id.dict()
        user = await users_collection.find_one(query)

        if user is not None:
            return UserID(**user)

    async def create_user(
            self,
            database_name: str,
            discord_id: DiscordUserID = None,
    ) -> Union[None, UserID]:
        users_collection = self.get_collection(database_name, USERS_COLLECTION_NAME)

        user_id = UserID(
            uuid=str(uuid.uuid4()), discord_id=discord_id
        )
        await users_collection.insert_one(user_id.dict())
        return user_id

    async def close(self):
        logger.info("Closing MongoDatabaseManager connection")
        self._client.close()

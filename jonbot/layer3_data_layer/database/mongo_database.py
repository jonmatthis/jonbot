import uuid
from typing import Union, List, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne, DESCENDING

from jonbot import get_logger
from jonbot.models.context_memory_document import ContextMemoryDocument
from jonbot.models.conversation_models import MessageHistory, ChatMessage
from jonbot.models.database_request_response_models import UpsertContextMemoryRequest, UpsertDiscordMessageRequest
from jonbot.models.discord_stuff.discord_id import DiscordUserID
from jonbot.models.discord_stuff.discord_message import DiscordMessageDocument
from jonbot.models.user_stuff.user_ids import TelegramUserID, UserID
from jonbot.system.environment_variables import MONGO_URI, USERS_COLLECTION_NAME, \
    RAW_MESSAGES_COLLECTION_NAME, CONTEXT_MEMORIES_COLLECTION_NAME

logger = get_logger()


class MongoDatabaseManager:
    def __init__(self):
        logger.info(f'Initializing MongoDatabaseManager...')
        self._client = AsyncIOMotorClient(MONGO_URI)

    def _get_database(self, database_name: str):
        return self._client[database_name]

    def _get_collection(self, database_name: str, collection_name: str):
        database = self._get_database(database_name)
        return database[collection_name]

    async def _upsert_many(self,
                           database_name: str,
                           entries: List[Dict[str, dict]],
                           collection_name: str) -> bool:
        operations = [
            UpdateOne(entry['query'], {"$set": entry['data']}, upsert=True)
            for entry in entries
        ]
        collection = self._get_collection(
            database_name=database_name, collection_name=collection_name
        )
        try:
            await collection.bulk_write(operations)
            return True
        except Exception as e:
            logger.error(f'Error occurred while upserting. Error: {e}')
            return False

    async def _get_sorted_documents(self,
                                    database_name: str,
                                    collection_name: str,
                                    query: dict,
                                    sort_field: str,
                                    limit: int = None,
                                    sort_order: int = DESCENDING) -> list:
        try:
            collection = self._get_collection(
                database_name=database_name, collection_name=collection_name
            )
            cursor = collection.find(query).sort(sort_field, sort_order)

            # Apply the limit if specified
            if limit is not None:
                cursor = cursor.limit(limit)

            documents = await cursor.to_list(length=None)
            return documents
        except Exception as e:
            logger.error(f'Error occurred while fetching and sorting documents. Error: {e}')
            return []



    async def upsert_discord_messages(self,
                                      upsert_discord_message_requests: List[UpsertDiscordMessageRequest]) -> bool:
        entries = [
            {"data": upsert_discord_message_request.data.dict(),
             "query": upsert_discord_message_request.query}
            for upsert_discord_message_request in upsert_discord_message_requests
        ]

        database_name = upsert_discord_message_requests[0].database_name
        if not all(upsert_discord_message_request.database_name == database_name for upsert_discord_message_request in
                   upsert_discord_message_requests):
            raise Exception("All upsert_discord_message_requests must have the same database_name")

        return await self._upsert_many(database_name=upsert_discord_message_requests[0].database_name,
                                       entries=entries,
                                       collection_name=RAW_MESSAGES_COLLECTION_NAME,
                                       )

    async def upsert_context_memory(self,
                                    upsert_context_memory_request: UpsertContextMemoryRequest) -> bool:

        entry = [{"data": upsert_context_memory_request.data.dict(),
                  "query": upsert_context_memory_request.query}]

        return await self._upsert_many(database_name=upsert_context_memory_request.database_name,
                                       entries=entry,
                                       collection_name=CONTEXT_MEMORIES_COLLECTION_NAME)

    async def get_message_history(self,
                                  database_name: str,
                                  context_route_query: dict,
                                  limit_messages: int = None) -> MessageHistory:

        documents = await self._get_sorted_documents(database_name=database_name,
                                   collection_name=RAW_MESSAGES_COLLECTION_NAME,
                                   query=context_route_query,
                                   sort_field="timestamp.unix_timestamp_utc",
                                   limit=limit_messages,
                                   sort_order=DESCENDING)

        message_history = MessageHistory()
        message_count = 0
        for document in documents:
            discord_message_document = DiscordMessageDocument(**document)
            chat_message = ChatMessage.from_discord_message_document(discord_message_document)
            message_history.add_message(chat_message)
        return message_history

    async def get_context_memory(self,
                                 database_name: str,
                                 context_route_query: dict,
                                 ) -> Optional[ContextMemoryDocument]:
        messages_collection = self._get_collection(database_name, CONTEXT_MEMORIES_COLLECTION_NAME)
        query = {"context_route_query": context_route_query}
        result = await messages_collection.find_one(query)

        if result is None:
            logger.warning(f"Context memory not found for context route: {context_route_query}")
            return None

        return ContextMemoryDocument(**result)


    async def get_or_create_user(self,
                                 database_name: str,
                                 discord_id: DiscordUserID = None,
                                 telegram_id: TelegramUserID = None) -> str:
        user = await self.get_user(database_name, discord_id=discord_id, telegram_id=telegram_id)
        if user is None:
            logger.debug(f"User not found. Creating new user.")
            user = await self.create_user(database_name, discord_id=discord_id, telegram_id=telegram_id)
        if user is None:
            logger.error(f"Failed to create user.")
            raise Exception(f"Failed to create user.")
        logger.success(f"User found: {user}")
        return user.uuid

    async def get_user(self,
                       database_name: str,
                       discord_id: DiscordUserID = None,
                       telegram_id: TelegramUserID = None) -> Union[None, UserID]:
        users_collection = self._get_collection(database_name, USERS_COLLECTION_NAME)

        query = {}
        if discord_id is not None:
            query["discord_id"] = discord_id.dict()
        if telegram_id is not None:
            query["telegram_id"] = telegram_id.dict()
        user = await users_collection.find_one(query)

        if user is not None:
            return UserID(**user)
    async def create_user(self,
                          database_name: str,
                          discord_id: DiscordUserID = None,
                          telegram_id: TelegramUserID = None) -> Union[None, UserID]:
        users_collection = self._get_collection(database_name, USERS_COLLECTION_NAME)

        user_id = UserID(uuid=str(uuid.uuid4()), discord_id=discord_id, telegram_id=telegram_id)
        await users_collection.insert_one(user_id.dict())
        return user_id

    async def close(self):
        logger.info("Closing MongoDatabaseManager connection")
        self._client.close()

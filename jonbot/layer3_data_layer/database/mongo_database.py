import uuid
from typing import Union

from motor.motor_asyncio import AsyncIOMotorClient

from jonbot import get_logger
from jonbot.models.context_memory_document import ContextMemoryDocument
from jonbot.models.conversation_models import MessageHistory, ChatMessage
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

    async def upsert(self,
                     database_name: str,
                     data: dict,
                     collection_name: str,
                     query: dict) -> bool:
        """Upsert data into the specified collection.

        This method will update an existing entry if it matches the query or insert a new one if it does not.

        Args:
            database_name (str): The name of the database to interact with.
            data (dict): The data to insert or update.
            collection_name (str): The name of the collection to interact with.
            query (dict, optional): The query to match the existing entry. Defaults to an empty dictionary.

        Returns:
            bool: True if the upsert operation was successful, False otherwise.
        """
        update_data = {"$set": data}
        collection = self._get_collection(database_name=database_name, collection_name=collection_name)
        try:
            await collection.update_one(query, update_data, upsert=True)
            return True
        except Exception as e:
            logger.error(f'Error occurred while upserting. Error: {e}')
            return False

    async def get_message_history(self,
                                  database_name: str,
                                  context_route_query: dict,
                                  limit_messages: int = None) -> MessageHistory:
        messages_collection = self._get_collection(database_name, RAW_MESSAGES_COLLECTION_NAME)
        query = {"context_route_query": context_route_query}
        result = messages_collection.find(query)
        messge_history = MessageHistory()
        message_count = 0
        async for document in result:
            if limit_messages is not None and message_count >= limit_messages:
                break
            message_count += 1
            discord_message_document = DiscordMessageDocument(**document)
            chat_message = ChatMessage.from_discord_message_document(discord_message_document)
            messge_history.add_message(chat_message)
        return messge_history

    async def get_context_memory(self,
                                 database_name: str,
                                 context_route_query: dict,
                                 ) -> ContextMemoryDocument:
        messages_collection = self._get_collection(database_name, CONTEXT_MEMORIES_COLLECTION_NAME)
        query = {"context_route_query": context_route_query}
        result = await messages_collection.find_one(query)

        if result is not None:
            return ContextMemoryDocument(**result)

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

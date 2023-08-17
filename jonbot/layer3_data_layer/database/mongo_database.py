import logging
import uuid
from typing import Union

from motor.motor_asyncio import AsyncIOMotorClient

from jonbot import get_logger
from jonbot.models.conversation_models import ConversationHistory
from jonbot.models.context_models import ContextRoute
from jonbot.models.discord_stuff.discord_id import DiscordUserID
from jonbot.models.user_stuff.user_ids import TelegramUserID, UserID
from jonbot.system.environment_variables import MONGO_URI, USERS_COLLECTION_NAME, \
    CONVERSATION_HISTORY_COLLECTION_NAME, DISCORD_MESSAGES_COLLECTION_NAME

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
                     query: dict = None) -> bool:
        if not query:
            query = {}
        update_data = {"$set": data}
        collection_name = self._get_collection(database_name=database_name,
                                               collection_name=collection_name)
        try:
            await collection_name.update_one(query, update_data, upsert=True)
            return True
        except Exception as e:
            logging.error(f'Error occurred while upserting. Error: {e}')
            return False

    async def get_conversation_history(self,
                                       database_name: str,
                                       context_route: dict) -> ConversationHistory:
        conversation_collection = self._get_collection(database_name, DISCORD_MESSAGES_COLLECTION_NAME)
        query = {"context_route": context_route}
        result =  conversation_collection.find(query)
        conversation_history = ConversationHistory()
        async for document in result:
            conversation_history.add_message(document)
        return conversation_history


    async def create_user(self,
                          database_name: str,
                          discord_id: DiscordUserID = None,
                          telegram_id: TelegramUserID = None) -> Union[None, UserID]:
        users_collection = self._get_collection(database_name, USERS_COLLECTION_NAME)

        user_id = UserID(uuid=str(uuid.uuid4()), discord_id=discord_id, telegram_id=telegram_id)
        await users_collection.insert_one(user_id.dict())
        return user_id

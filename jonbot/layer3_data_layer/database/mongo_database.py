import logging
import uuid
from typing import Union

from motor.motor_asyncio import AsyncIOMotorClient

from jonbot.models.conversation_models import ContextRoute, ConversationHistory
from jonbot.models.user_id_models import DiscordUserID, TelegramUserID, UserID
from jonbot.system.environment_variables import MONGO_URI, DATABASE_NAME, USERS_COLLECTION_NAME, \
    CONVERSATION_HISTORY_COLLECTION_NAME
from jonbot.system.logging.get_or_create_logger import logger


class MongoDatabaseManager:
    def __init__(self):
        logger.info(f'Initializing MongoDatabaseManager...')
        self._client = AsyncIOMotorClient(MONGO_URI)
        self._database = self._client[DATABASE_NAME]
        self._users_collection = self._database[USERS_COLLECTION_NAME]
        self._conversation_history_collection = self._database[CONVERSATION_HISTORY_COLLECTION_NAME]

    async def get_or_create_user(self,
                                 discord_id: DiscordUserID = None,
                                 telegram_id: TelegramUserID = None) -> str:

        user = await self.get_user(discord_id=discord_id,
                                   telegram_id=telegram_id)
        if user is None:
            logger.debug(f"User not found. Creating new user.")
            user = await self.create_user(discord_id=discord_id,
                                          telegram_id=telegram_id)
        return user.uuid

    async def get_user(self,
                       discord_id: DiscordUserID = None,
                       telegram_id: TelegramUserID = None) -> Union[None, UserID]:
        query = {}
        if discord_id is not None:
            query["discord_id"] = discord_id.dict()
        if telegram_id is not None:
            query["telegram_id"] = telegram_id.dict()
        user = await self._users_collection.find_one(query)

        if user is not None:
            return UserID(**user)

    async def upsert(self,
                     data: dict,
                     collection: str,
                     query: dict = None) -> bool:

        if not query:
            query = {}

        update_data = {"$set": data}

        try:
            await self._database[collection].update_one(query, update_data, upsert=True)
            return True
        except Exception as e:
            logging.error(f'Error occurred while upserting. Error: {e}')
            return False

    async def get_conversation_history(self,
                                       context_route: ContextRoute) -> dict:
        query = {"context_route": context_route.dict()}
        result = await self._conversation_history_collection.find_one(query)

        return ConversationHistory(**result) if result is not None else None

    async def create_user(self,
                          discord_id: DiscordUserID = None,
                          telegram_id: TelegramUserID = None) -> Union[None, UserID]:
        user_id = UserID(uuid=str(uuid.uuid4()),
                         discord_id=discord_id,
                         telegram_id=telegram_id)
        await self._users_collection.insert_one(user_id.dict())
        return user_id

    async def test_startup(self):

        test_collection_name = 'test_collection'
        test_uuid = str(uuid.uuid4())
        test_doc = {'uuid': test_uuid,
                    'test_field': 'test_value'}
        logger.debug(f'Running Mongo Database startup test...')
        try:
            logger.debug(f"Creating test collection: {test_collection_name}")
            test_collection = self._database[test_collection_name]
            if test_collection is not None:
                logger.debug(f'Successfully created test collection.')
            else:
                raise Exception(f'Failed to create test collection.')

            logger.debug(f'Inserting test document: {test_doc}')
            result = await test_collection.insert_one(test_doc)
            if result.inserted_id is not None:
                logger.debug(f'Successfully inserted test document.')
            else:
                raise Exception(f'Failed to insert test document.')

            retrieved_doc = await test_collection.find_one({'uuid': test_uuid})
            if retrieved_doc is not None:
                logger.debug(f'Successfully retrieved test document ({retrieved_doc}).')
            else:
                raise Exception(f'Failed to retrieve test document.')

            delete_result = await test_collection.delete_one({'uuid': test_uuid})
            if delete_result.deleted_count == 1:
                logger.debug(f'Successfully deleted test document.')
            else:
                raise Exception(f'Failed to delete test document.')

            logger.debug(f'Mongo Database startup test successful.')

        except Exception as e:
            logging.error(f'Startup test unsuccessful :( ')
            logging.exception(e)
            raise

        logger.debug(f'MongoDatabaseManager Startup test complete :D')

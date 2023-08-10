import json
import logging
import os
import traceback
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Union

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from jonbot.layer3_data_layer.data_models.conversation_models import ConversationHistory, ContextRoute
from jonbot.layer3_data_layer.data_models.user_id_models import TelegramID, DiscordID, UserID
from jonbot.layer3_data_layer.system.filenames_and_paths import clean_path_string, get_default_database_json_save_path
from jonbot.layer3_data_layer.utilities.default_serialize import default_serialize

logger = logging.getLogger(__name__)

DATA_COLLECTION_NAME = "jonbot_collection"
USERS_COLLECTION_NAME = "jonbot_users"
CONVERSATION_HISTORY_COLLECTION_NAME = "conversation_history"
DATABASE_NAME = "jonbot_database"


class MongoDatabaseManager:
    def __init__(self):
        logger.info(f'Initializing MongoDatabaseManager...')
        load_dotenv()
        # self._client = MongoClient( os.getenv('MONGO_URI_MONGO_CLOUD'))
        self._client = AsyncIOMotorClient(os.getenv('MONGO_URI_MONGO_CLOUD'))
        self._database = self._client[DATABASE_NAME]
        self._data_collection = self._database[DATA_COLLECTION_NAME]
        self._users_collection = self._database[USERS_COLLECTION_NAME]
        self._conversation_history_collection = self._database[CONVERSATION_HISTORY_COLLECTION_NAME]

    async def test_startup(self):
        logger.debug(f'Running startup test...')
        test_uuid = str(uuid.uuid4())
        test_doc = {'uuid': test_uuid,
                    'test_field': 'test_value'}
        try:
            result = await self._data_collection.insert_one(test_doc)
            assert result.inserted_id is not None

            retrieved_doc = await self._data_collection.find_one({'uuid': test_uuid})
            assert retrieved_doc == test_doc

            delete_result = await self._data_collection.delete_one({'uuid': test_uuid})
            assert delete_result.deleted_count > 0

            logger.debug(f'Successful startup test.')

        except Exception as e:
            logging.error(f'Startup test unsuccessful.')
            logging.error(e)

        logger.debug(f'Startup test complete.')

    async def get_or_create_user(self,
                                 discord_id: DiscordID = None,
                                 telegram_id: TelegramID = None) -> str:

        user = await self.get_user(discord_id=discord_id,
                                   telegram_id=telegram_id)
        if user is None:
            logger.debug(f"User not found. Creating new user.")
            user = await self.create_user(discord_id=discord_id,
                                          telegram_id=telegram_id)
        return user.uuid

    async def get_user(self,
                       discord_id: DiscordID = None,
                       telegram_id: TelegramID = None) -> Union[None, UserID]:
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
                     collection: str = None,
                     query: dict = None)->bool:

        if not query:
            query = {}

        update_data = {"$set": data}

        try:
            if  collection:
                await self._database[collection].update_one(query, update_data, upsert=True)
            else:
                await self._data_collection.update_one(query, update_data, upsert=True)
            return True
        except Exception as e:
            logging.error(f'Error occurred while upserting. Error: {e}')
            return False


    async def get_conversation_history(self,
                                       context_route: ContextRoute)->dict:
        query = {"context_route": context_route.dict()}
        result = await self._conversation_history_collection.find_one(query)

        return ConversationHistory(**result) if result is not None else None

    async def save_to_json(self,
                           query: dict = None,
                           save_path: Union[str, Path] = None):

        logger.info(f"Saving data to database")

        try:
            query = query if query is not None else defaultdict()

            if save_path is not None:
                file_name = Path(save_path).name
                if file_name.endswith(".json"):
                    file_name = file_name[:-5]
                file_name = clean_path_string(file_name)
                save_path = Path(save_path).parent / file_name
            else:
                save_path = get_default_database_json_save_path(filename=f"{self._data_collection.name}_backup",
                                                                timestamp=True)

            data = [doc for doc in self._data_collection.find(query)]

            save_path = str(save_path)
            if save_path[-5:] != ".json":
                save_path += ".json"

            for document in data:
                document["_id"] = str(document["_id"])
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'w') as file:
                json.dump(data, file, indent=4, default=default_serialize)
        except Exception as e:
            traceback.print_exc()
            print(f"Error saving json: {e}")
            raise

        logger.info(f"Saved {len(data)} documents to {save_path}")

    async def create_user(self,
                          discord_id: DiscordID = None,
                          telegram_id: TelegramID = None) -> Union[None, UserID]:
        user_id = UserID(uuid=str(uuid.uuid4()),
                         discord_id=discord_id,
                         telegram_id=telegram_id)
        await self._users_collection.insert_one(user_id.dict())
        return user_id




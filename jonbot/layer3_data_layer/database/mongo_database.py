import json
import logging
import os
import traceback
from collections import defaultdict
from pathlib import Path
from typing import Union

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from jonbot.layer3_data_layer.system.filenames_and_paths import clean_path_string, get_default_database_json_save_path
from jonbot.layer3_data_layer.utilities.default_serialize import default_serialize

logger = logging.getLogger(__name__)

BASE_COLLECTION_NAME = "jonbot_collection"
DATABASE_NAME = "jonbot_database"



class MongoDatabaseManager:
    def __init__(self):
        logger.info(f"Connecting to MongoDB...")
        load_dotenv()
        # self._client = MongoClient( os.getenv('MONGO_URI_MONGO_CLOUD'))
        self._client = AsyncIOMotorClient(os.getenv('MONGO_URI_MONGO_CLOUD'))
        self._database = self._client[DATABASE_NAME]
        self._collection = self._database[BASE_COLLECTION_NAME]

    async def upsert(self, data: dict, collection_name: str = None, query: dict = None):
        """
        Upsert data into the database.

        Args:
            data (dict): The data to upsert.
            collection_name (str, optional): The name of the collection. Defaults to None.
            query (dict, optional): The query to filter data. Defaults to {}.

        Returns:
            UpdateResult: Result of the upsert operation.
        """
        logger.debug(f"Upserting data to database")

        if not query:
            query = {}

        update_data = {"$set": data}
        if collection_name:
            return self._collection.update_one(query, update_data, upsert=True)
        else:
            return self._database[collection_name].update_one(query, update_data, upsert=True)

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
                save_path = get_default_database_json_save_path(filename=f"{self._collection.name}_backup",
                                                                timestamp=True)

            data = [doc for doc in self._collection.find(query)]

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
            raise e

        logger.info(f"Saved {len(data)} documents to {save_path}")


mongo_database_manager = MongoDatabaseManager()

if __name__ == "__main__":
    try:
        # Creating an instance of MongoDatabase to test the connection
        mongo_database = MongoDatabaseManager()
        logger.info("Successfully connected to MongoDB!")

        # Creating a test user and conversation ID
        test_user_id = "test_user_123"
        test_conversation_id = "test_conversation_123"

        # Logging the test user and conversation
        mongo_database.log_user(user_id=test_user_id)
        mongo_database.log_conversation(conversation_id=test_conversation_id)
        logger.info(f"Successfully logged test user: {test_user_id} and test conversation: {test_conversation_id}")
    except Exception as e:
        # Log any exceptions that occur during the connection or logging
        logger.error(f"Failed to connect or write to MongoDB: {e}")
    finally:
        # Close the connection to the MongoDB client
        if 'mongo_database' in locals() and hasattr(mongo_database, '_client'):
            mongo_database._client.close()
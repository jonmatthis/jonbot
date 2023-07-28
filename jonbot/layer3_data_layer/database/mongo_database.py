import json
import logging
import os
import traceback
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Union

from pydantic import BaseModel
from pymongo import MongoClient

from jonbot.layer3_data_layer.data_models.application_data_model import ApplicationDataModel
from jonbot.layer3_data_layer.data_models.conversation_models import ChatInteraction
from jonbot.layer3_data_layer.database.abstract_database import AbstractDatabase
from jonbot.layer3_data_layer.system.filenames_and_paths import clean_path_string, get_default_database_json_save_path

logger = logging.getLogger(__name__)

BASE_COLLECTION_NAME = "all_data"
DATABASE_NAME = "jonbot"


def get_mongo_uri() -> str:
    remote_uri = os.getenv('MONGO_URI_MONGO_CLOUD')
    if remote_uri:
        return remote_uri

    is_docker = os.getenv('IS_DOCKER', False)
    if is_docker:
        return os.getenv('MONGO_URI_DOCKER')
    else:
        return os.getenv('MONGO_URI_LOCAL')



class MongoDatabase(AbstractDatabase):
    def __init__(self):
        logger.info(f"Connecting to MongoDB...")
        self._client = MongoClient(get_mongo_uri())
        self._database = self._client[DATABASE_NAME]
        self._collection = self._database[BASE_COLLECTION_NAME]

    def log_user(self, user_id: str):
        logger.info(f"Logging user: {user_id}")
        self._database.users.insert_one({"_id": user_id})

    def log_conversation(self, conversation_id: str):
        logger.info(f"Logging conversation: {conversation_id}")
        self._database.conversations.insert_one({"_id": conversation_id})

    def add_interaction_to_conversation(self, conversation_id: str, interaction: ChatInteraction):
        logger.info(f"Adding interaction {interaction.uuid} to conversation: {conversation_id}")
        self._database.conversations.update_one({"_id": conversation_id},
                                                {"$push": {"interactions": interaction.model_dump_json()}})

    def load_data(self) -> ApplicationDataModel:
        logger.info(f"Loading data from database")
        users = list(self._database.users.find())
        conversations = list(self._database.conversations.find())
        settings = None
        logger.info(f"Loaded {len(users)} users, {len(conversations)} conversations. Settings: {settings}")
        return ApplicationDataModel(users=users,
                                    conversations=conversations,
                                    settings=settings)

    def save_data(self,
                  data: BaseModel,
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

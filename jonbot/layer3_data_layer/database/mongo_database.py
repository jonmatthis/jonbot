import os
from collections import defaultdict
from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pymongo import MongoClient

from jonbot.layer3_data_layer.data_models.application_data_model import ApplicationDataModel
from jonbot.layer3_data_layer.data_models.conversation_models import ChatInteraction
from jonbot.layer3_data_layer.database.abstract_database import AbstractDatabase


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
        self._client = MongoClient(get_mongo_uri())
        self._database = self._client['jonbot']



    def log_user(self, user_id: str):
        self._database.users.insert_one({"_id": user_id})

    def log_conversation(self, conversation_id: str):
        self._database.conversations.insert_one({"_id": conversation_id})

    def add_interaction_to_conversation(self, conversation_id: str, interaction: ChatInteraction):
        self._database.conversations.update_one({"_id": conversation_id},
                                                {"$push": {"interactions": interaction.model_dump_json()}})


    def load_data(self) -> ApplicationDataModel:
        users = list(self._database.users.find())
        conversations = list(self._database.conversations.find())
        settings = None
        return ApplicationDataModel(users=users,
                                    conversations=conversations,
                                    settings=settings)

    def save_data(self, data: BaseModel):
        pass
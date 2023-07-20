from abc import ABC, abstractmethod

from pydantic import BaseModel

from jonbot.layer3_data_layer.data_models.application_data_model import ApplicationDataModel
from jonbot.layer3_data_layer.data_models.conversation_models import ChatInteraction


class AbstractDatabase(ABC):
    @abstractmethod
    def log_user(self, user_id: str):
        pass

    @abstractmethod
    def log_conversation(self, conversation_id: str):
        pass

    @abstractmethod
    def add_interaction_to_conversation(self, conversation_id: str, interaction: ChatInteraction):
        pass

    @abstractmethod
    def save_data(self, data: BaseModel):
        pass

    @abstractmethod
    def load_data(self) -> ApplicationDataModel:
        pass

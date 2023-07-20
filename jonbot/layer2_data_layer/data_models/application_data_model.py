from typing import Dict

from pydantic import BaseModel, Field

from jonbot.layer2_data_layer.data_models.conversation_models import ConversationModel
from jonbot.layer2_data_layer.data_models.user_data_model import UserModel


class SettingsModel:
    pass


class ApplicationDataModel(BaseModel):

    users: Dict[str, UserModel] = Field(default_factory=dict,
                                        description = "Dictionary of all users key is `user_id (str(uuid.uuid4()))` value is `UserModel`")

    conversations: Dict[str, ConversationModel] = Field(default_factory=dict,
                                                        description = "Dictionary of all conversations key is `conversation_id (str(uuid.uuid4()))` value is `ConversationModel`")

    settings: SettingsModel = Field(default_factory=SettingsModel,
                                    description = "Settings for the application")
    class Config:
        arbitrary_types_allowed = True
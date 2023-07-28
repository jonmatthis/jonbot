import uuid
from typing import Any

from pydantic import BaseModel, Field

from jonbot.layer3_data_layer.data_models.timestamp_model import Timestamp


class ChatInput(BaseModel):
    message: str
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict = {}


class ChatResponse(BaseModel):
    message: str
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict = {}


class ChatInteraction(BaseModel):
    human_input: ChatInput
    bot_response: ChatResponse
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))

    class Config:
        arbitrary_types_allowed = True


class ConversationModel(BaseModel):
    interactions: list[ChatInteraction] = []
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))

    def model_post_init(self, __context: Any) -> None:
        self.uuid = str(uuid.uuid4())



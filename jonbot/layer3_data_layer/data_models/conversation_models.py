import uuid
from collections import OrderedDict
from typing import Union, Optional

from pydantic import BaseModel, Field

from jonbot.layer3_data_layer.data_models.timestamp_model import Timestamp


class ConversationalContext(BaseModel):
    context_route: str = "The human is talking to your through an unknown interface."
    context_description: str = "You are having a conversation with a human."


# TODO - replace all use of ChatInput and ChatReponse with ChatMessage
class ChatInput(BaseModel):
    message: str
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict = {}


class ChatResponse(BaseModel):
    message: str
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict = {}


class Speaker(BaseModel):
    name: str
    id: Optional[Union[int, str]]
    type: str


class ChatMessage(BaseModel):
    message: str
    speaker: Speaker
    timestamp: Timestamp
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict = {}


class ConversationHistory(BaseModel):
    history: OrderedDict[str, ChatMessage] = Field(default_factory=OrderedDict)
    context_route: Optional[str] = ''
    def add_message(self, chat_message: ChatMessage):
        speaker = chat_message.speaker
        self.history[f"{speaker.type}||{speaker.name}||{chat_message.uuid}"] = chat_message

    def get_all_messages(self) -> OrderedDict[str, ChatMessage]:
        return self.history

    def __len__(self):
        return len(self.history)

class ChatRequestConfig(BaseModel):
    dummy: str = "hi:D"


class ChatRequest(BaseModel):
    chat_input: ChatInput
    conversational_context: ConversationalContext = ConversationalContext()
    config: ChatRequestConfig = ChatRequestConfig()
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))

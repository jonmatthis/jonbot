import uuid
from typing import Any

from pydantic import BaseModel, Field



class ChatInput(BaseModel):
    message: str
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict = {}




class ChatRequest(BaseModel):
    chat_input: ChatInput
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    config: dict = {}


class ChatResponse(BaseModel):
    message: str
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict = {}



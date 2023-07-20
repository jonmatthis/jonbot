import time
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from tzlocal import get_localzone


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


class Timestamp(BaseModel):
    unix_timestamp_utc: float = datetime.utcnow().timestamp()
    unix_timestamp_local: float = datetime.now().timestamp()
    unix_timestamp_utc_isoformat: str = datetime.utcnow().isoformat()
    unix_timestamp_local_isoformat: str = datetime.now().isoformat()
    perf_counter_ns: int = time.perf_counter_ns()
    local_time_zone: str = get_localzone().key

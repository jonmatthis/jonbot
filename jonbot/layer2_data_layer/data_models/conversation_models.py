import time
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ChatInput(BaseModel):
    message: str
    uuid: str
    metadata: dict = {}
    def model_post_init(self, __context: Any) -> None:
        self.uuid = str(uuid.uuid4())
class ChatResponse(BaseModel):
    message: str
    uuid: str
    metadata: dict = {}
    def model_post_init(self, __context: Any) -> None:
        self.uuid = str(uuid.uuid4())
class ChatInteraction(BaseModel):
    human_input: ChatInput
    bot_response: ChatResponse

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, __context: Any) -> None:
        self.uuid = self.human_input.uuid + self.bot_response.uuid
class ConversationModel(BaseModel):
    interactions: list[ChatInteraction] = []
    uuid: str

    def model_post_init(self, __context: Any) -> None:
        self.uuid = str(uuid.uuid4())
class Timestamp(BaseModel):
    unix_timestamp_utc: Any = datetime.utcnow().timestamp()
    unix_timestamp_local: Any = datetime.now().timestamp()
    unix_timestamp_utc_isoformat: Any = datetime.utcnow().isoformat()
    unix_timestamp_local_isoformat: Any = datetime.now().isoformat()
    unix_timestamp_utc_string: Any = str(datetime.utcnow()),
    perf_counter_ns: Any = time.perf_counter_ns()

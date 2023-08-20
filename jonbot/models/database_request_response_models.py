from typing import Literal

from pydantic import BaseModel, validator

from jonbot import get_logger
from jonbot.models.context_memory_document import ContextMemoryDocument
from jonbot.models.context_route import ContextRoute
from jonbot.models.conversation_models import ChatRequest
from jonbot.models.discord_stuff.discord_message import DiscordMessageDocument

logger = get_logger()

class MessageHistoryRequest(BaseModel):
    context_route: ContextRoute
    database_name: str
    limit_messages: int = None

    @classmethod
    def from_chat_request(cls, chat_request: ChatRequest):
        return cls(context_route=chat_request.context_route,
                   limit_messages=chat_request.config.limit_messages)

    @property
    def query(self):
        return self.context_route.as_query


class ContextMemoryRequest(BaseModel):
    data: ContextMemoryDocument
    database_name: str
    type: Literal["upsert", "get"] = None

    @validator("type", always=True, pre=True)
    def set_type(cls, v, values: dict):
        try:
            if values.get("data"):
                if len(values["data"].message_buffer) > 0:
                    return "upsert"
                else:
                    return "get"
        except Exception as e:
            logger.exception(e)
            raise
    @classmethod
    def from_context_route(cls, context_route: ContextRoute, database_name: str):
        return cls(data=ContextMemoryDocument(context_route=context_route),
                   database_name=database_name)
    @property
    def query(self):
        return self.data.query


class UpsertDiscordMessageRequest(BaseModel):
    data: DiscordMessageDocument
    database_name: str

    @property
    def query(self):
        return self.data.query


class DiscordMessageResponse(BaseModel):
    success: bool

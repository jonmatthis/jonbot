from pydantic import BaseModel

from jonbot.models.context_memory_document import ContextMemoryDocument
from jonbot.models.context_route import ContextRoute
from jonbot.models.conversation_models import ChatRequest
from jonbot.models.discord_stuff.discord_message import DiscordMessageDocument
from jonbot.system.environment_variables import RAW_MESSAGES_COLLECTION_NAME


class LogMessageRequest(BaseModel):
    database_name: str
    collection_name: str
    data: dict
    query: dict


class LogDiscordMessageResponse(BaseModel):
    success: bool


class MessageHistoryRequest(BaseModel):
    database_name: str
    context_route: ContextRoute
    limit_messages: int = None

    @classmethod
    def from_chat_request(cls, chat_request: ChatRequest):
        return cls(database_name=chat_request.database_name,
                   context_route=chat_request.context_route,
                   limit_messages=chat_request.config.limit_messages)



class UpsertContextMemoryRequest(BaseModel):
    data: ContextMemoryDocument
    database_name: str
    query: dict


class UpsertDiscordMessageRequest(BaseModel):
    data: DiscordMessageDocument
    database_name: str
    query: dict

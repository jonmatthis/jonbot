from pydantic import BaseModel

from jonbot.models.context_memory_document import ContextMemoryDocument
from jonbot.models.context_route import ContextRoute
from jonbot.models.conversation_models import ChatRequest
from jonbot.system.environment_variables import RAW_MESSAGES_COLLECTION_NAME


class DatabaseUpsertRequest(BaseModel):
    database_name: str
    collection_name: str
    data: dict
    query: dict


class DatabaseUpsertResponse(BaseModel):
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


class UpdateContextMemoryRequest(BaseModel):
    context_memory_document: ContextMemoryDocument
    database_name: str
    context_route: ContextRoute

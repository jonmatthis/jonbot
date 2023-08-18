from pydantic import BaseModel

from jonbot.models.context_route import ContextRoute
from jonbot.models.conversation_models import ChatRequest
from jonbot.system.environment_variables import MEMORIES_COLLECTION_NAME, RAW_MESSAGES_COLLECTION_NAME


class DatabaseUpsertRequest(BaseModel):
    database_name: str
    collection_name: str
    data: dict
    query: dict


class DatabaseUpsertResponse(BaseModel):
    success: bool


class ConversationHistoryRequest(BaseModel):
    database_name: str
    memories_collection_name: str = MEMORIES_COLLECTION_NAME
    raw_messages_collection_name: str = RAW_MESSAGES_COLLECTION_NAME
    context_route: ContextRoute
    limit_messages: int = None
    @classmethod
    def from_chat_request(cls, chat_request: ChatRequest):
        return cls(database_name=chat_request.database_name,
                   context_route=chat_request.context_route,
                   limit_messages=chat_request.config.limit_messages)


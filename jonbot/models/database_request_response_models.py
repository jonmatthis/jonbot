from pydantic import BaseModel

from jonbot.models.context_route import ContextRoute


class DatabaseUpsertRequest(BaseModel):
    database_name: str
    collection_name: str
    data: dict
    query: dict


class DatabaseUpsertResponse(BaseModel):
    success: bool


class ConversationHistoryRequest(BaseModel):
    database_name: str
    context_route: ContextRoute

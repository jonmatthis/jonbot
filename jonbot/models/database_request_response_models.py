from typing import Literal, List, Dict, Any, Optional

from langchain import PromptTemplate
from pydantic import BaseModel

from jonbot import get_logger
from jonbot.models.context_memory_document import ContextMemoryDocument
from jonbot.models.context_route import ContextRoute
from jonbot.models.conversation_models import ChatRequest
from jonbot.models.discord_stuff.discord_message import DiscordMessageDocument

logger = get_logger()


class MessageHistoryResponse(BaseModel):
    success: bool
    data: List[DiscordMessageDocument] = None


class MessageHistoryRequest(BaseModel):
    context_route: ContextRoute
    database_name: str
    limit_messages: int = None

    @classmethod
    def from_chat_request(cls, chat_request: ChatRequest):
        return cls(
            context_route=chat_request.context_route,
            limit_messages=chat_request.config.limit_messages,
        )

    @property
    def query(self):
        return self.context_route.as_query


class ContextMemoryDocumentResponse(BaseModel):
    success: bool
    data: ContextMemoryDocument = None


class ContextMemoryDocumentRequest(BaseModel):
    data: ContextMemoryDocument
    database_name: str
    query: Dict[str, Any]
    request_type: Literal["upsert", "get"] = None

    @classmethod
    def build_upsert_request(cls, document: ContextMemoryDocument, database_name: str):
        return cls(
            data=document,
            database_name=database_name,
            query=document.query,
            request_type="upsert" if document.message_buffer is None else "get",
        )

    @classmethod
    def build_get_request(
        cls,
        context_route: ContextRoute,
        database_name: str,
        summary_prompt: Optional[PromptTemplate] = None,
    ):
        return cls(
            data=ContextMemoryDocument.build_empty(
                context_route=context_route, summary_prompt=summary_prompt
            ),
            database_name=database_name,
            query=context_route.as_query,
            request_type="get",
        )


class UpsertDiscordMessagesRequest(BaseModel):
    data: List[DiscordMessageDocument]
    query: List[Dict[str, Any]]
    database_name: str

    @classmethod
    def from_discord_message_documents(
        cls, documents: List[DiscordMessageDocument], database_name: str
    ):
        query = [message.query for message in documents]
        return cls(data=documents, query=query, database_name=database_name)


class UpsertDiscordMessagesResponse(BaseModel):
    success: bool

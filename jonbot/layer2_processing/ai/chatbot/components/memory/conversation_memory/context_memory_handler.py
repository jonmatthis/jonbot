from typing import Optional, List

from langchain import PromptTemplate
from langchain.schema import BaseMessage
from pydantic import BaseModel

from jonbot import get_logger
from jonbot.layer2_processing.backend_database_operator.backend_database_operator import (
    BackendDatabaseOperations,
)
from jonbot.models.context_memory_document import ContextMemoryDocument
from jonbot.models.context_route import ContextRoute
from jonbot.models.conversation_models import ChatRequest
from jonbot.models.database_request_response_models import ContextMemoryDocumentRequest

logger = get_logger()


class ContextMemoryHandler(BaseModel):
    context_route: ContextRoute
    database_operations: BackendDatabaseOperations
    database_name: str
    current_context_memory_document: ContextMemoryDocument = None

    @classmethod
    def build(
        cls,
        chat_request: ChatRequest,
        database_operations: BackendDatabaseOperations,
    ):
        return cls(
            context_route=chat_request.context_route,
            database_name=chat_request.database_name,
            database_operations=database_operations,
        )

    async def get_context_memory_document(self) -> ContextMemoryDocument:
        if self.current_context_memory_document is None:
            logger.trace(
                f"Current context memory document is None, loading from database..."
            )
            self.current_context_memory_document = await self._load_context_memory()
        if self.current_context_memory_document is None:
            logger.warning(
                f"Current context memory document was not found in database, returning empty document..."
            )
            self.current_context_memory_document = ContextMemoryDocument.build_empty(
                context_route=self.context_route, summary_prompt=self.summary_prompt
            )
        if self.current_context_memory_document is None:
            raise Exception("Failed to load a context memory docyument...")

        return self.current_context_memory_document

    async def update(
        self,
        message_buffer: List[BaseMessage],
        summary: str,
        summary_prompt: PromptTemplate,
        token_count: int,
    ):
        logger.debug(
            f"Updating context memory for context route: {self.context_route.dict()} - summary: {summary}"
        )
        document = await self.get_context_memory_document()
        document.update(
            message_buffer=message_buffer,
            summary=summary,
            tokens_count=token_count,
            summary_prompt=summary_prompt,
        )
        await self._upsert_context_memory()

    async def _load_context_memory(self) -> Optional[ContextMemoryDocument]:
        logger.info(
            f"Loading context memory for context route: {self.context_route.dict()} from database: {self.database_name}..."
        )
        get_request = ContextMemoryDocumentRequest.build_get_request(
            context_route=self.context_route,
            database_name=self.database_name,
        )
        response = await self.database_operations.get_context_memory_document(
            request=get_request
        )

        if not response.success:
            logger.warning(
                f"Could not load context memory from database for context route: {get_request.query}"
            )
            return

        return response.data

    @property
    async def _upsert_request(self) -> ContextMemoryDocumentRequest:
        document = await self.get_context_memory_document()
        return ContextMemoryDocumentRequest.build_upsert_request(
            document=document, database_name=self.database_name
        )

    async def _upsert_context_memory(self):
        logger.debug(
            f"Upserting context memory for context route: {self.context_route.dict()}"
        )
        try:
            await self.database_operations.upsert_context_memory(
                await self._upsert_request
            )
        except Exception as e:
            logger.exception(e)
            raise

from typing import Optional

from langchain import PromptTemplate
from pydantic import BaseModel

from jonbot.layer2_processing.backend_database_operator.backend_database_operator import (
    BackendDatabaseOperations,
)
from jonbot.models.context_memory_document import ContextMemoryDocument
from jonbot.models.context_route import ContextRoute
from jonbot.models.database_request_response_models import ContextMemoryDocumentRequest
from jonbot.system.setup_logging.get_logger import get_jonbot_logger

logger = get_jonbot_logger()


class ContextMemoryHandler(BaseModel):
    context_route: ContextRoute
    current_context_memory_document: ContextMemoryDocument = None
    database_operations: BackendDatabaseOperations
    database_name: str
    summary_prompt: PromptTemplate

    @property
    async def context_memory_document(self) -> ContextMemoryDocument:
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
        return self.current_context_memory_document

    async def _load_context_memory(self) -> Optional[ContextMemoryDocument]:
        logger.info(
            f"Loading context memory for context route: {self.context_route.dict()} from database: {self.database_name}..."
        )
        get_request = ContextMemoryDocumentRequest.build_get_request(
            context_route=self.context_route,
            summary_prompt=self.summary_prompt,
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
        document = await self.context_memory_document
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

    async def update(self, message_buffer: list, summary: str, token_count: int):
        logger.debug(
            f"Updating context memory for context route: {self.context_route.dict()} - summary: {summary}"
        )
        document = await self.context_memory_document
        document.update(
            message_buffer=message_buffer, summary=summary, tokens_count=token_count
        )
        await self._upsert_context_memory()

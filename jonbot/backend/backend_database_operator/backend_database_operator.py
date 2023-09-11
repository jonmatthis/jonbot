from typing import Optional

from pydantic import BaseModel

from jonbot.backend.data_layer.database.mongo_database import MongoDatabaseManager
from jonbot.backend.data_layer.models.database_request_response_models import (
    UpsertDiscordMessagesResponse,
    MessageHistoryRequest,
    ContextMemoryDocumentRequest,
    UpsertDiscordMessagesRequest,
    ContextMemoryDocumentResponse,
    MessageHistoryResponse,
)
from jonbot.system.setup_logging.get_logger import get_jonbot_logger

logger = get_jonbot_logger()


class BackendDatabaseOperations(BaseModel):
    mongo_database: MongoDatabaseManager

    class Config:
        arbitrary_types_allowed = True

    async def upsert_discord_messages(
            self, request: UpsertDiscordMessagesRequest
    ) -> UpsertDiscordMessagesResponse:
        logger.info(
            f"Upserting {len(request.data)} messages to database: {request.database_name} with query: {request.query}"
        )

        success = await self.mongo_database.upsert_discord_messages(request=request)
        if success:
            return UpsertDiscordMessagesResponse(success=True)
        else:
            return UpsertDiscordMessagesResponse(success=False)

    async def get_message_history_document(
            self, request: MessageHistoryRequest
    ) -> MessageHistoryResponse:
        logger.info(
            f"Getting conversation history for context route: {request.context_route.dict()}"
        )
        message_history = await self.mongo_database.get_message_history(request=request)

        if message_history is None:
            logger.warning(
                f"Conversation history not found for context route: {request.context_route.dict()}"
            )
            return MessageHistoryResponse(success=False)

        return MessageHistoryResponse(success=True, data=message_history)

    async def get_context_memory_document(
            self, request: ContextMemoryDocumentRequest
    ) -> Optional[ContextMemoryDocumentResponse]:
        if request.request_type == "upsert":
            raise Exception(
                "get_context_memory_document should not be called with request type: upsert"
            )

        logger.info(
            f"Retrieving context memory for context route: {request.data.context_route.as_flat_dict}"
        )
        document = await self.mongo_database.get_context_memory(request=request)
        if document is None:
            logger.warning(
                f"Context memory not found for context route: {request.data.context_route.as_flat_dict}"
            )
            return ContextMemoryDocumentResponse(success=False)

        return ContextMemoryDocumentResponse(success=True, data=document)

    async def upsert_context_memory(self, request: ContextMemoryDocumentRequest):
        logger.info(
            f"Updating context memory for context route: {request.data.context_route.dict()}"
        )
        success = await self.mongo_database.upsert_context_memory(
            request=request,
        )
        if success:
            logger.success(
                f"Successfully updated context memory for context route: {request.data.context_route.dict()}"
            )
        else:
            logger.error(
                f"Error occurred while updating context memory for context route: {request.data.context_route.dict()}"
            )

    async def close(self):
        logger.info("Closing database connection...")
        await self.mongo_database.close()
        logger.info("Database connection closed!")

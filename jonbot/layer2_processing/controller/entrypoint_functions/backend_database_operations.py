from typing import Optional

from pydantic import BaseModel

from jonbot import get_logger
from jonbot.layer3_data_layer.database.get_or_create_mongo_database_manager import get_or_create_mongo_database_manager
from jonbot.layer3_data_layer.database.mongo_database import MongoDatabaseManager
from jonbot.models.context_memory_document import ContextMemoryDocument
from jonbot.models.conversation_models import MessageHistory
from jonbot.models.database_request_response_models import UpsertDiscordMessagesResponse, \
    MessageHistoryRequest, ContextMemoryRequest, UpsertDiscordMessagesRequest

logger = get_logger()


class BackendDatabaseOperations(BaseModel):
    mongo_database: MongoDatabaseManager

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    async def build(cls):
        mongo_database = await get_or_create_mongo_database_manager()
        return cls(mongo_database=mongo_database)

    async def upsert_discord_messages(self,
                                      request: UpsertDiscordMessagesRequest) -> UpsertDiscordMessagesResponse:
        logger.info(f"Upserting {len(request.data)} messages to database: {request.database_name} with query: {request.query}")

        success = await self.mongo_database.upsert_discord_messages(
            request=request)
        if success:
            return UpsertDiscordMessagesResponse(success=True)
        else:
            return UpsertDiscordMessagesResponse(success=False)

    async def get_message_history_document(self,
                                           request: MessageHistoryRequest) -> MessageHistory:
        logger.info(
            f"Getting conversation history for context route: {request.context_route.dict()}")
        message_history = await self.mongo_database.get_message_history(request=request)

        return message_history

    async def get_context_memory_document(self,
                                          request: ContextMemoryRequest) -> Optional[ContextMemoryDocument]:
        if request.request_type == "upsert":
            raise Exception("get_context_memory_document should not be called with request type: upsert")

        logger.info(
            f"Retrieving context memory for context route: {request.data.context_route.as_flat_dict}")
        context_memory_document = await self.mongo_database.get_context_memory(request=request)
        if context_memory_document is None:
            logger.warning(f"Context memory not found for context route: {request.data.context_route.as_flat_dict}")
            return None

        return context_memory_document

    async def upsert_context_memory(self, request: ContextMemoryRequest):
        logger.info(
            f"Updating context memory for context route: {request.data.context_route.dict()}")
        success = await self.mongo_database.upsert_context_memory(request=request, )
        if success:
            logger.success(
                f"Successfully updated context memory for context route: {request.data.context_route.dict()}")
        else:
            logger.error(
                f"Error occurred while updating context memory for context route: {request.data.context_route.dict()}")

    async def close(self):
        logger.info("Closing database connection...")
        await self.mongo_database.close()
        logger.info("Database connection closed!")

from pydantic import BaseModel

from jonbot import get_logger
from jonbot.layer3_data_layer.database.get_or_create_mongo_database_manager import get_or_create_mongo_database_manager
from jonbot.layer3_data_layer.database.mongo_database import MongoDatabaseManager
from jonbot.models.context_memory_document import ContextMemoryDocument
from jonbot.models.context_route import ContextRoute
from jonbot.models.conversation_models import MessageHistory
from jonbot.models.database_request_response_models import LogDiscordMessageResponse, \
    MessageHistoryRequest, UpsertContextMemoryRequest, UpsertDiscordMessageRequest

logger = get_logger()


class BackendDatabaseOperations(BaseModel):
    mongo_database: MongoDatabaseManager

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    async def build(cls):
        mongo_database = await get_or_create_mongo_database_manager()
        return cls(mongo_database=mongo_database)

    async def upsert_discord_message(self,
                                     upsert_discord_message_request: UpsertDiscordMessageRequest) -> LogDiscordMessageResponse:
        logger.info(f"Logging message in database: Message id: {upsert_discord_message_request.data.message_id},"
                    f" content: {upsert_discord_message_request.data.content}")
        success = await self.mongo_database.upsert_discord_messages(
            upsert_discord_message_requests=[upsert_discord_message_request])
        if success:
            return LogDiscordMessageResponse(success=True)
        else:
            return LogDiscordMessageResponse(success=False)

    async def get_message_history_document(self,
                                           message_history_request: MessageHistoryRequest) -> MessageHistory:
        logger.info(
            f"Getting conversation history for context route: {message_history_request.context_route.dict()}")
        message_history = await self.mongo_database.get_message_history(
            database_name=message_history_request.database_name,
            context_route_query=message_history_request.context_route.as_query,
            limit_messages=message_history_request.limit_messages, )
        return message_history

    async def get_context_memory_document(self,
                                          context_route: ContextRoute,
                                          database_name: str) -> ContextMemoryDocument:
        logger.info(
            f"Retrieving context memory for context route: {context_route.dict()}")
        context_memory_document = await self.mongo_database.get_context_memory(
            database_name=database_name,
            context_route_query=context_route.as_query,
        )
        return context_memory_document

    async def upsert_context_memory(self, upsert_context_memory_request: UpsertContextMemoryRequest):
        logger.info(
            f"Updating context memory for context route: {upsert_context_memory_request.data.context_route.dict()}")
        await self.mongo_database.upsert_context_memory(upsert_context_memory_request=upsert_context_memory_request, )

    async def close(self):
        logger.info("Closing database connection...")
        await self.mongo_database.close()
        logger.info("Database connection closed!")

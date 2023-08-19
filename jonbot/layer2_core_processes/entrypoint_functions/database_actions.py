from jonbot import get_logger
from jonbot.layer3_data_layer.database.get_or_create_mongo_database_manager import get_or_create_mongo_database_manager
from jonbot.models.context_memory_document import ContextMemoryDocument
from jonbot.models.context_route import ContextRoute
from jonbot.models.conversation_models import MessageHistory
from jonbot.models.database_request_response_models import DatabaseUpsertRequest, DatabaseUpsertResponse, \
    MessageHistoryRequest

logger = get_logger()


async def database_upsert(database_upsert_request: DatabaseUpsertRequest) -> DatabaseUpsertResponse:
    logger.info(f"Upserting data into database query - {database_upsert_request.query}")
    mongo_database = await get_or_create_mongo_database_manager()
    success = await mongo_database.upsert(**database_upsert_request.dict())
    if success:
        return DatabaseUpsertResponse(success=True)
    else:
        return DatabaseUpsertResponse(success=False)


async def get_message_history_document(message_history_request: MessageHistoryRequest) -> MessageHistory:
    logger.info(
        f"Getting conversation history for context route: {message_history_request.context_route.dict()}")
    mongo_database = await get_or_create_mongo_database_manager()
    message_history = await mongo_database.get_message_history(
        database_name=message_history_request.database_name,
        context_route_query=message_history_request.context_route.as_query, )
    return message_history


async def get_context_memory_document(context_route: ContextRoute,
                                      database_name: str) -> ContextMemoryDocument:
    logger.info(
        f"Retrieving context memory for context route: {context_route.dict()}")
    mongo_database = await get_or_create_mongo_database_manager()
    context_memory_document = await mongo_database.get_context_memory(
        database_name=database_name,
        context_route_query=context_route.as_query,
    )
    return context_memory_document

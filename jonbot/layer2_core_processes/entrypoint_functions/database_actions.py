from jonbot import get_logger
from jonbot.layer3_data_layer.database.get_or_create_mongo_database_manager import get_or_create_mongo_database_manager
from jonbot.models.conversation_models import ConversationHistory
from jonbot.models.database_request_response_models import DatabaseUpsertRequest, DatabaseUpsertResponse, \
    ConversationHistoryRequest

logger = get_logger()


async def database_upsert(database_upsert_request: DatabaseUpsertRequest) -> DatabaseUpsertResponse:
    logger.info(f"Upserting data into database query - {database_upsert_request.query}")
    mongo_database = await get_or_create_mongo_database_manager()
    success = await mongo_database.upsert(**database_upsert_request.dict())
    if success:
        return DatabaseUpsertResponse(success=True)
    else:
        return DatabaseUpsertResponse(success=False)


async def get_conversation_history(conversation_history_request: ConversationHistoryRequest) -> ConversationHistory:
    logger.info(
        f"Getting conversation history for context route: {conversation_history_request.context_route.dict()}")
    mongo_database = await get_or_create_mongo_database_manager()
    conversation_history = await mongo_database.get_conversation_history(
        database_name=conversation_history_request.database_name,
        context_route_query=conversation_history_request.context_route.as_query,
        limit_messages=conversation_history_request.limit_messages,)
    return conversation_history


async def get_conversation_history_from_chat_request(chat_request):
    conversation_history_request = ConversationHistoryRequest(database_name=chat_request.database_name,
                                                              context_route=chat_request.context_route,
                                                              limit_messages=chat_request.config.limit_messages)
    conversation_history = await get_conversation_history(conversation_history_request=conversation_history_request)
    return conversation_history

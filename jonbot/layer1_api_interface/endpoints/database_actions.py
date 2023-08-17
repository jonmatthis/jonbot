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
    logger.info(f"Getting conversation history for context route: {conversation_history_request.context_route.dict()}")
    mongo_database = await get_or_create_mongo_database_manager()
    conversation_history = await mongo_database.get_conversation_history(**conversation_history_request.dict())
    return conversation_history

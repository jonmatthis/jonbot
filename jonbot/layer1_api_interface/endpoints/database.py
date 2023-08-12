from jonbot.layer3_data_layer.database.get_or_create_mongo_database_manager import get_or_create_mongo_database_manager
from jonbot.models.database_upsert_models import DatabaseUpsertRequest, DatabaseUpsertResponse

from jonbot.system.logging.get_or_create_logger import logger
async def database_upsert(database_upsert_request: DatabaseUpsertRequest) -> DatabaseUpsertResponse:
    logger.info(f"Upserting data into database query - {database_upsert_request.query}")
    mongo_database = await get_or_create_mongo_database_manager()
    success = await mongo_database.upsert(**database_upsert_request.dict())
    if success:
        return DatabaseUpsertResponse(success=True)
    else:
        return DatabaseUpsertResponse(success=False)

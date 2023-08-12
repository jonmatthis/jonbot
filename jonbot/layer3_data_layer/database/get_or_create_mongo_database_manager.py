from jonbot.layer3_data_layer.database.mongo_database import MongoDatabaseManager
from jonbot.system.logging.configure_logging import logger

MONGO_DATABASE_MANAGER = None

async def get_or_create_mongo_database_manager() -> MongoDatabaseManager:
    global MONGO_DATABASE_MANAGER
    if MONGO_DATABASE_MANAGER is None:
        logger.info("Creating new MongoDatabaseManager instance")
        MONGO_DATABASE_MANAGER = MongoDatabaseManager()
        await MONGO_DATABASE_MANAGER.test_startup()
    return MONGO_DATABASE_MANAGER

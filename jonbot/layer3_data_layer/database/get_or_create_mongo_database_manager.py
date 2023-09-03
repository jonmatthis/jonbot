from jonbot.layer3_data_layer.database.mongo_database import MongoDatabaseManager
from jonbot.layer3_data_layer.utilities.run_mongo_test import run_mongo_test
from jonbot.system.setup_logging.get_logger import get_jonbot_logger

logger = get_jonbot_logger()

MONGO_DATABASE_MANAGER = None


async def get_mongo_database_manager() -> MongoDatabaseManager:
    global MONGO_DATABASE_MANAGER
    if MONGO_DATABASE_MANAGER is None:
        logger.info("Creating new MongoDatabaseManager instance")
        MONGO_DATABASE_MANAGER = MongoDatabaseManager()
        if not await run_mongo_test(MONGO_DATABASE_MANAGER):
            logger.error("MongoDatabaseManager startup test failed.")
            raise Exception("MongoDatabaseManager startup test failed.")
        logger.success("MongoDatabaseManager created and startup tests passed!")
    return MONGO_DATABASE_MANAGER


async def close_mongo_database_manager():
    global MONGO_DATABASE_MANAGER
    if MONGO_DATABASE_MANAGER is not None:
        await MONGO_DATABASE_MANAGER.close()
        MONGO_DATABASE_MANAGER = None

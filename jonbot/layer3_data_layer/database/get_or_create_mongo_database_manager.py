import logging

from jonbot.layer3_data_layer.database.mongo_database import MongoDatabaseManager
from jonbot.layer3_data_layer.utilities.run_mongo_test import run_mongo_test

from jonbot import get_logger
logger = get_logger()

MONGO_DATABASE_MANAGER = None


async def get_or_create_mongo_database_manager() -> MongoDatabaseManager:
    global MONGO_DATABASE_MANAGER
    if MONGO_DATABASE_MANAGER is None:
        logger.info("Creating new MongoDatabaseManager instance")
        MONGO_DATABASE_MANAGER = MongoDatabaseManager()
        assert await run_mongo_test(MONGO_DATABASE_MANAGER), "MongoDatabaseManager startup test failed."
    return MONGO_DATABASE_MANAGER

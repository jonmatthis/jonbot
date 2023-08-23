import logging
import uuid

from jonbot import get_logger
from jonbot.layer3_data_layer.database.get_or_create_mongo_database_manager import (
    get_mongo_database_manager,
)
from jonbot.layer3_data_layer.database.mongo_database import MongoDatabaseManager

logger = get_logger()


async def test_mongo_database(
    manager: MongoDatabaseManager = get_mongo_database_manager(),
    database_name: str = "test_database",
):
    test_collection_name = "test_collection"
    test_uuid = str(uuid.uuid4())
    test_doc = {"uuid": test_uuid, "test_field": "test_value"}

    logger.debug(f"Running Mongo Database startup test...")

    try:
        logger.debug(f"Creating test collection: {test_collection_name}")
        test_collection = manager._get_collection(database_name, test_collection_name)
        if test_collection is not None:
            logger.debug(f"Successfully created test collection.")
        else:
            raise Exception(f"Failed to create test collection.")

        logger.debug(f"Inserting test document: {test_doc}")
        result = await test_collection.insert_one(test_doc)
        if result.inserted_id is not None:
            logger.debug(f"Successfully inserted test document.")
        else:
            raise Exception(f"Failed to insert test document.")

        retrieved_doc = await test_collection.find_one({"uuid": test_uuid})
        if retrieved_doc is not None:
            logger.debug(f"Successfully retrieved test document ({retrieved_doc}).")
        else:
            raise Exception(f"Failed to retrieve test document.")

        delete_result = await test_collection.delete_one({"uuid": test_uuid})
        if delete_result.deleted_count == 1:
            logger.debug(f"Successfully deleted test document.")
        else:
            raise Exception(f"Failed to delete test document.")

        logger.debug(f"Mongo Database startup test successful.")

    except Exception as e:
        logging.error(f"Startup test unsuccessful :( ")
        logging.exception(e)
        raise

    logger.debug(f"MongoDatabaseManager Startup test complete :D")
    return True

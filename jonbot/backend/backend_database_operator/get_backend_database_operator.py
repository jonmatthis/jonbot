from jonbot.backend.data_layer.database.mongo_database import MongoDatabaseManager
from jonbot.backend.backend_database_operator.backend_database_operator import (
    BackendDatabaseOperations,
)
from jonbot.system.setup_logging.get_logger import get_jonbot_logger

logger = get_jonbot_logger()

BACKEND_DATABASE_OPERATOR = None


def get_backend_database_operator(
        mongo_database: MongoDatabaseManager,
) -> BackendDatabaseOperations:
    global BACKEND_DATABASE_OPERATOR
    if BACKEND_DATABASE_OPERATOR is None:
        logger.info("Creating BackendDatabaseOperator")
        BACKEND_DATABASE_OPERATOR = BackendDatabaseOperations(
            mongo_database=mongo_database
        )
    return BACKEND_DATABASE_OPERATOR

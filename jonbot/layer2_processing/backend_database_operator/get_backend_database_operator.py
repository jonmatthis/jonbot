from jonbot import get_logger
from jonbot.layer2_processing.backend_database_operator.backend_database_operator import \
    BackendDatabaseOperations
from jonbot.layer3_data_layer.database.mongo_database import MongoDatabaseManager

logger = get_logger()

BACKEND_DATABASE_OPERATOR = None


def get_backend_database_operator(mongo_database: MongoDatabaseManager) -> BackendDatabaseOperations:
    global BACKEND_DATABASE_OPERATOR
    if BACKEND_DATABASE_OPERATOR is None:
        logger.info("Creating BackendDatabaseOperator")
        BACKEND_DATABASE_OPERATOR = BackendDatabaseOperations(mongo_database=mongo_database)
    return BACKEND_DATABASE_OPERATOR

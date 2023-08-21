from jonbot import get_logger
from jonbot.layer2_processing.backend_database_operator.backend_database_operator import \
    BackendDatabaseOperations
from jonbot.layer2_processing.controller.controller import Controller

logger = get_logger()

CONTROLLER = None


def get_controller(database_operator: BackendDatabaseOperations) -> Controller:
    global CONTROLLER
    if CONTROLLER is None:
        logger.info("Creating Controller...")
        CONTROLLER = Controller(database_operations=database_operator)
    return CONTROLLER

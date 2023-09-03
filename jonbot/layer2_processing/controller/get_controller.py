from jonbot.layer2_processing.backend_database_operator.backend_database_operator import (
    BackendDatabaseOperations,
)
from jonbot.layer2_processing.controller.controller import Controller
from jonbot.system.setup_logging.get_logger import get_jonbot_logger

logger = get_jonbot_logger()

CONTROLLER = None


def get_controller(database_operator: BackendDatabaseOperations) -> Controller:
    global CONTROLLER
    if CONTROLLER is None:
        logger.info("Creating Controller...")
        CONTROLLER = Controller(database_operations=database_operator)
    return CONTROLLER

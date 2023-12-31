from jonbot.api_interface.api_client.api_client import ApiClient
from jonbot.system.setup_logging.get_logger import get_jonbot_logger

logger = get_jonbot_logger()

API_CLIENT = None


def get_or_create_api_client() -> ApiClient:
    global API_CLIENT
    if API_CLIENT is None:
        logger.info("Creating new ApiClient instance")
        API_CLIENT = ApiClient()
    return API_CLIENT

import logging

from jonbot.layer1_api_interface.api_client.api_client import ApiClient

logger = logging.getLogger(__name__)

API_CLIENT = None


def get_or_create_api_client() -> "ApiClient":
    global API_CLIENT
    if API_CLIENT is None:
        logger.info("Creating new ApiClient instance")
        API_CLIENT = ApiClient()
    return API_CLIENT


api_client = get_or_create_api_client()

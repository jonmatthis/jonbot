import logging

from jonbot.layer1_api_interface.api_client.api_client import ApiClient

from jonbot import get_logger
logger = get_logger()

API_CLIENT = None


def get_or_create_api_client() -> ApiClient:
    global API_CLIENT
    if API_CLIENT is None:
        logger.info("Creating new ApiClient instance")
        API_CLIENT = ApiClient()
    return API_CLIENT




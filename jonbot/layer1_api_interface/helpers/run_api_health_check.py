import asyncio
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

from jonbot.layer1_api_interface.api_client.get_or_create_api_client import api_client
from jonbot.layer1_api_interface.routes import HEALTH_ENDPOINT

from jonbot import get_logger
logger = get_logger()

@retry(
    stop=stop_after_attempt(60),
    wait=wait_exponential(multiplier=1, max=60)  # start waiting for 1s, then double with each retry to a maximum of 60s
)
async def run_api_health_check():
    logger.info("Checking API health...")

    try:
        response = await api_client.send_request_to_api(endpoint_name=HEALTH_ENDPOINT, type="GET")
        if response["status"] == "alive":
            logger.info(f"API is alive! \n {response}")
            return
        else:
            logger.info("API is not alive yet. Retrying...")
    except Exception as e:
        logger.exception(f"Health check returned an error: {str(e)}")
        raise  # Re-raise the exception to trigger a retry

    raise Exception("API is not alive after max attempts. Aborting.")

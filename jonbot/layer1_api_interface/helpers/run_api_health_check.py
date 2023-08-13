import asyncio
import logging

from jonbot.layer1_api_interface.api_client.get_or_create_api_client import api_client
from jonbot.layer1_api_interface.routes import HEALTH_ENDPOINT

logger = logging.getLogger(__name__)


async def run_api_health_check(attempts: int = 60):
    logger.info("Checking API health...")
    for attempt_number in range(attempts):
        logger.info(f"Checking API health (attempt {attempt_number + 1} of {attempts})")
        try:
            response = await api_client.send_request_to_api(endpoint_name=HEALTH_ENDPOINT, type="GET")
            if response["status"] == "alive":
                logger.info(f"API is alive! \n {response}")
                return
            else:
                logger.info(
                    f"API is not alive yet. Waiting for 1 second before checking again (`{attempts - attempt_number}` attempts remaining)")
                await asyncio.sleep(1)
        except Exception as e:
            logger.exception(f"Health check returned an error: {str(e)}")

    raise Exception(f"API is not alive after {attempts} attempts. Aborting.")

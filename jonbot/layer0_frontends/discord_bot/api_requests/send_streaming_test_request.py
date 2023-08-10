import asyncio
import logging

from jonbot.layer1_api_interface.app import STREAMING_RESPONSE_TEST_ENDPOINT
from jonbot.layer1_api_interface.send_request_to_api import send_request_to_api_streaming

logger = logging.getLogger(__name__)

async def print_over_here(token):
    await asyncio.sleep(1)
    logger.debug(f"frontend got token: {token}")


async def streaming_response_test_endpoint():
    return await send_request_to_api_streaming(api_endpoint=STREAMING_RESPONSE_TEST_ENDPOINT,
                                               data={"test": "test"},
                                               callbacks=[print_over_here])


if __name__ == '__main__':
    asyncio.run(streaming_response_test_endpoint())

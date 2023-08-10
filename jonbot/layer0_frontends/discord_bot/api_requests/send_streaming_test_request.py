import asyncio

from jonbot.layer1_api_interface.app import STREAMING_RESPONSE_TEST_ENDPOINT, get_api_endpoint_url
from jonbot.layer1_api_interface.send_request_to_api import send_request_to_api_streaming


async def print_over_here(token):
    await asyncio.sleep(1)
    print(token)


async def streaming_response_test_endpoint():
    return await send_request_to_api_streaming(api_route=get_api_endpoint_url(STREAMING_RESPONSE_TEST_ENDPOINT),
                                               data={"test": "test"},
                                               callbacks=[print_over_here])

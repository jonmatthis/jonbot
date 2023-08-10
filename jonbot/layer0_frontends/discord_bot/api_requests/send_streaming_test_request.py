import asyncio

import discord

from jonbot.layer1_api_interface.app import STREAMING_RESPONSE_TEST_ENDPOINT, get_api_endpoint_url
from jonbot.layer1_api_interface.send_request_to_api import send_request_to_api_streaming


async def print_over_here(token):
    await asyncio.sleep(1)
    print(token)


async def streaming_response_test_endpoint(message: discord.Message = None):
    if not message:
        return await send_request_to_api_streaming(api_route=get_api_endpoint_url(STREAMING_RESPONSE_TEST_ENDPOINT),
                                               data={"test": "test"},
                                               callbacks=[print_over_here])
    else:
        return await send_request_to_api_streaming(api_route=get_api_endpoint_url(STREAMING_RESPONSE_TEST_ENDPOINT),
                                               data={"test": "test"},
                                               callbacks=[message.channel.send])

if __name__ == '__main__':
    asyncio.run(streaming_response_test_endpoint())
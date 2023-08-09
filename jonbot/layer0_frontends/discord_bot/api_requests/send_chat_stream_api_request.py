import asyncio

import aiohttp

from jonbot.layer1_api_interface.app import API_CHAT_STREAM_URL


async def send_chat_stream_api_request():
    async with aiohttp.ClientSession() as session:
        async with session.get(API_CHAT_STREAM_URL) as response:
            async for line in response.content:
                print(line.decode('utf-8').strip())




if __name__ == '__main__':
    asyncio.run(send_chat_stream_api_request())
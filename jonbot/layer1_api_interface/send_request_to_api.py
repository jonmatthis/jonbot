import logging
from typing import Callable

import aiohttp

logger = logging.getLogger(__name__)


async def send_request_to_api(api_route: str,
                              data: dict, ) -> dict:
    async with aiohttp.ClientSession() as session:
        response = await session.post(api_route, json=data)

        if response.status == 200:
            return await response.json()
        else:
            error_message = await error_message_from_response(response)
            logger.exception(error_message)
            raise Exception(error_message)


async def send_request_to_api_streaming(api_route: str,
                                        data: dict,
                                        callbacks: Callable) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.post(api_route) as response:
            async for line in response.content:
                for callback in callbacks:
                    callback(line.decode('utf-8').strip())

        if response.status == 200:
            return await response.json()
        else:
            error_message = await error_message_from_response(response)
            logger.exception(error_message)
            raise Exception(error_message)


async def error_message_from_response(response):
    error_message = f"Received non-200 response code: {response.status} - {await response.text()}"
    return error_message

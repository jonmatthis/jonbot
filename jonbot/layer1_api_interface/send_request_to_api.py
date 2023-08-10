import asyncio
import logging
from typing import Callable, Coroutine, Union, List

import aiohttp

from jonbot.layer3_data_layer.data_models.conversation_models import ChatRequest

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
                                        callbacks: Union[Callable, Coroutine]=None) -> dict:

    if not callbacks:
        callbacks = []

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_route, json=data) as response:
                if response.status == 200:
                    async for line in response.content:
                        await run_callbacks(callbacks, line)
                else:
                    error_message = await error_message_from_response(response)
                    logger.error(error_message)
                    await run_callbacks(callbacks, error_message.encode('utf-8'))
                    raise Exception(error_message)
    except Exception as e:
        error_msg = f"An error occurred while streaming from the API: {str(e)}"
        logger.exception(error_msg)
        await run_callbacks(callbacks, error_msg.encode('utf-8'))
        raise e


async def run_callbacks(callbacks: List[Callable], line: bytes):
    try:
        for callback in callbacks:
            if asyncio.iscoroutinefunction(callback):
                await callback(line.decode('utf-8').strip())
            else:
                callback(line.decode('utf-8').strip())
    except Exception as e:
        logger.exception(f"An error occurred while running a callback: {str(e)}")
        raise e


async def error_message_from_response(response):
    error_message = f"Received non-200 response code: {response.status} - {await response.text()}"
    return error_message

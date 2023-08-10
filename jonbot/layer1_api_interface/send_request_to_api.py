import asyncio
import logging
from typing import Callable, Coroutine, Union, List

import aiohttp

from jonbot.layer1_api_interface.app import get_api_endpoint_url

logger = logging.getLogger(__name__)


async def send_request_to_api(api_route: str = None,
                              api_endpoint: str = None,
                              data: dict = None,
                              type: str = "POST") -> dict:
    api_route = handle_api_route_input(api_endpoint=api_endpoint,
                                       api_route=api_route)

    if not data:
        data = {}

    async with aiohttp.ClientSession() as session:
        if type == "POST":
            response = await session.post(api_route, json=data)
        elif type == "GET":
            response = await session.get(api_route, json=data)
        else:
            raise Exception(f"Invalid type: {type}")

        if response.status == 200:
            return await response.json()
        else:
            error_message = await error_message_from_response(response)
            logger.exception(error_message)
            raise Exception(error_message)


def handle_api_route_input(api_endpoint, api_route) -> str:
    if not api_route:
        if not api_endpoint:
            raise Exception("Must provide either api_route or api_endpoint")

        api_route = get_api_endpoint_url(api_endpoint)
    else:
        if api_endpoint:
            raise Exception("Cannot provide both api_route and api_endpoint")
    return api_route


async def send_request_to_api_streaming(api_route: str = None,
                                        api_endpoint: str = None,
                                        data: dict = dict(),
                                        callbacks: Union[Callable, Coroutine] = None) -> list():
    if not callbacks:
        callbacks = []

    if not data:
        data = {}

    api_route = handle_api_route_input(api_endpoint=api_endpoint,
                                       api_route=api_route)

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
        raise


async def run_callbacks(callbacks: List[Callable], line: bytes):
    try:
        for callback in callbacks:
            logger.debug(f"Running callback: {callback.__name__}")
            if asyncio.iscoroutinefunction(callback):
                await callback(line.decode('utf-8').strip())
            else:
                callback(line.decode('utf-8').strip())
    except Exception as e:
        logger.exception(f"An error occurred while running a callback: {str(e)}")
        raise


async def error_message_from_response(response):
    error_message = f"Received non-200 response code: {response.status} - {await response.text()}"
    return error_message

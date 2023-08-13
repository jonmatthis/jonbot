import asyncio

import logging

logger = logging.getLogger(__name__)


async def generate_test_tokens():
    for chunk in range(10):
        test_token = f"Token {chunk}"
        logger.info(f"Streaming response test yielding token: {test_token}")
        yield f"Data {chunk}\n"
        await asyncio.sleep(1)  # simulate some delay

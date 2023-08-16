import asyncio
import logging

from uvicorn import Config, Server

from jonbot.layer1_api_interface.routes import get_or_create_fastapi_app
from jonbot.system.environment_variables import HOST_NAME, PORT_NUMBER

logger = logging.getLogger(__name__)

app = get_or_create_fastapi_app()


def run_api():
    """
    Run the API for jonbot
    """
    logger.info("Starting API")
    import uvicorn

    uvicorn.run(app, host=HOST_NAME, port=PORT_NUMBER)


async def run_api_async():
    """
    Run the API for jonbot
    """
    logger.info("Starting API")

    config = Config(app=app, host=HOST_NAME, port=PORT_NUMBER)
    server = Server(config)
    logger.info(
        f"Server: {server} - {server.config} - {server.config.app} - Started on {server.config.host}:{str(server.config.port)}")
    await server.serve()


def run_api_sync():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_api_async())


if __name__ == '__main__':
    asyncio.run(run_api_async())

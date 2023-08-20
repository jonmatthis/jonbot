import asyncio

from fastapi import FastAPI
from uvicorn import Config, Server

from jonbot import get_logger
from jonbot.layer1_api_interface.api_routes import register_api_routes
from jonbot.layer2_processing.controller.controller import Controller
from jonbot.layer2_processing.controller.entrypoint_functions.backend_database_operations import \
    BackendDatabaseOperations
from jonbot.system.environment_variables import HOST_NAME, PORT_NUMBER

logger = get_logger()

FAST_API_APP = None


async def get_or_create_fastapi_app():
    global FAST_API_APP
    if FAST_API_APP is None:
        FAST_API_APP = FastAPI()
        database_operations = await BackendDatabaseOperations.build()
        controller = Controller(database_operations=database_operations)
        register_api_routes(app=FAST_API_APP,
                            database_operations=database_operations,
                            controller=controller)
    return FAST_API_APP


async def run_api_async():
    """
    Run the API for jonbot
    """
    logger.info("Starting API")
    fastapi_app = await get_or_create_fastapi_app()
    config = Config(app=fastapi_app, host=HOST_NAME, port=PORT_NUMBER)
    server = Server(config)
    logger.success(
        f"Server: {server} - {server.config} - {server.config.app} - Started on {server.config.host}:{str(server.config.port)}")
    await server.serve()


def run_api_sync():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_api_async())


if __name__ == '__main__':
    asyncio.run(run_api_async())

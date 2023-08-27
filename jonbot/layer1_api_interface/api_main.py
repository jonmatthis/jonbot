import asyncio

from fastapi import FastAPI
from uvicorn import Config, Server

from jonbot import get_logger
from jonbot.layer1_api_interface.api_routes import register_api_routes
from jonbot.layer2_processing.backend_database_operator.get_backend_database_operator import (
    get_backend_database_operator,
)
from jonbot.layer2_processing.controller.get_controller import get_controller
from jonbot.layer3_data_layer.database.get_or_create_mongo_database_manager import (
    get_mongo_database_manager,
)
from jonbot.system.environment_variables import HOST_NAME, PORT_NUMBER

logger = get_logger()

FAST_API_APP = None


async def get_or_create_fastapi_app():
    global FAST_API_APP
    if FAST_API_APP is None:
        FAST_API_APP = FastAPI()

        mongo_database = await get_mongo_database_manager()
        database_operator = get_backend_database_operator(mongo_database=mongo_database)
        controller = get_controller(database_operator=database_operator)

        register_api_routes(
            app=FAST_API_APP,
            database_operations=database_operator,
            controller=controller,
        )

    return FAST_API_APP


async def run_api_async():
    """
    Run the API for jonbot
    """
    try:
        logger.info("Starting API")
        fastapi_app = await get_or_create_fastapi_app()
        config = Config(app=fastapi_app, host=HOST_NAME, port=PORT_NUMBER)
        server = Server(config)
        logger.success(
            f"Server: {server} - {server.config} - {server.config.app} - Started on {server.config.host}:{str(server.config.port)}"
        )
        await server.serve()
    except Exception as e:
        logger.exception(f"Failed to run API: {e}")
        raise e
    finally:
        logger.info("API stopped")
        get_mongo_database_manager().close()


def run_api_sync():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_api_async())


if __name__ == "__main__":
    asyncio.run(run_api_async())

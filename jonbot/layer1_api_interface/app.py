import asyncio
import logging
import os
from typing import List, Callable, Union, Coroutine

import aiohttp
from dotenv import load_dotenv
from fastapi import FastAPI
from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain.callbacks.base import AsyncCallbackHandler
from starlette.responses import StreamingResponse
from uvicorn import Config, Server

from jonbot.layer2_core_processes.ai_chatbot.ai_chatbot import AIChatBot
from jonbot.layer2_core_processes.audio_transcription.transcribe_audio import transcribe_audio
from jonbot.layer3_data_layer.data_models.conversation_models import ChatResponse, ChatRequest
from jonbot.layer3_data_layer.data_models.database_upsert_models import DatabaseUpsertResponse, DatabaseUpsertRequest
from jonbot.layer3_data_layer.data_models.health_check_status import HealthCheckResponse
from jonbot.layer3_data_layer.data_models.voice_to_text_request import VoiceToTextRequest, VoiceToTextResponse
from jonbot.layer3_data_layer.database.get_or_create_mongo_database_manager import get_or_create_mongo_database_manager

logger = logging.getLogger(__name__)

load_dotenv()

PREFIX = "http"
PORT_NUMBER = os.getenv("PORT_NUMBER", 8000)
HOST_NAME = "localhost"

HEALTH_ENDPOINT = "/health"
CHAT_ENDPOINT = "/chat"
CHAT_STREAM_ENDPOINT = "/chat_stream"
STREAMING_RESPONSE_TEST_ENDPOINT = "/test_streaming_response"
VOICE_TO_TEXT_ENDPOINT = "/voice_to_text"
DATABASE_UPSERT_ENDPOINT = "/database_upsert"


def get_api_url(host_name: str = HOST_NAME,
                prefix: str = PREFIX) -> str:
    return f"{prefix}://{host_name}"


def get_api_endpoint_url(api_endpoint: str,
                         host_name: str = HOST_NAME,
                         port_number: int = PORT_NUMBER,
                         prefix: str = PREFIX) -> str:
    if not api_endpoint.startswith("/"):
        api_endpoint = f"/{api_endpoint}"

    return f"{get_api_url(host_name=host_name, prefix=prefix)}:{port_number}{api_endpoint}"


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
                    async for line in response.content.iter_any():
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


async def health_check_api(attempts: int = 60):
    logger.info("Checking API health...")
    for attempt_number in range(attempts):
        logger.info(f"Checking API health (attempt {attempt_number + 1} of {attempts})")
        try:
            response = await send_request_to_api(get_api_endpoint_url(HEALTH_ENDPOINT),
                                                 type="GET")
            if response["status"] == "alive":
                logger.info(f"API is alive! \n {response}")
                return
            else:
                logger.info(
                    f"API is not alive yet. Waiting for 1 second before checking again (`{attempts - attempt_number}` attempts remaining)")
                await asyncio.sleep(1)
        except Exception as e:
            logger.info(f"Health check returned an error: {str(e)}")


    raise Exception(f"API is not alive after {attempts} attempts. Aborting.")


app = FastAPI()


@app.on_event("startup")
async def startup_event():
    logger.info("Starting up...")
    logger.info("Creating MongoDatabaseManager instance")
    await get_or_create_mongo_database_manager()
    logger.info("Startup complete!")


@app.get(HEALTH_ENDPOINT, response_model=HealthCheckResponse)
async def health_check():
    return HealthCheckResponse(status="alive")


@app.post(CHAT_ENDPOINT, response_model=ChatResponse)
async def chat(chat_request: ChatRequest) -> ChatResponse:
    logger.info(f"Received chat request: {chat_request}")

    mongo_database = await get_or_create_mongo_database_manager()
    conversation_history = await mongo_database.get_conversation_history(
        context_route=chat_request.conversation_context.context_route)

    ai_chat_bot = await AIChatBot.build(conversation_context=chat_request.conversation_context,
                                        conversation_history=conversation_history, )
    ai_chat_bot.add_callback_handler(StreamingStdOutCallbackHandler())
    chat_response = await ai_chat_bot.get_chat_response(chat_input_string=chat_request.chat_input.message)

    return chat_response


class StreamingAsyncCallbackHandler(AsyncCallbackHandler):
    async def on_llm_new_token(self, token: str, *args, **kwargs) -> None:
        """Run when a new token is generated."""
        print("Hi! I just woke up. Your llm is generating a new token: '{token}'")
        yield f"lookit this token: {token} |"


@app.post(CHAT_STREAM_ENDPOINT, response_class=StreamingResponse)
async def chat_stream(chat_request: ChatRequest):
    logger.info(f"Received chat_stream request: {chat_request}")

    mongo_database = await get_or_create_mongo_database_manager()
    conversation_history = await mongo_database.get_conversation_history(
        context_route=chat_request.conversation_context.context_route)

    ai_chat_bot = await AIChatBot.build(conversation_context=chat_request.conversation_context,
                                        conversation_history=conversation_history, )

    ai_chat_bot.add_callback_handler(handler=StreamingAsyncCallbackHandler())

    async def stream_response():
        async for token in ai_chat_bot.stream_chat_response_tokens(input_text=chat_request.chat_input.message):
            logger.debug(f"Streaming token: {token['text']}")
            yield token["text"]

    return StreamingResponse(stream_response(), media_type="text/plain")


@app.post(STREAMING_RESPONSE_TEST_ENDPOINT)
async def streaming_response_test():
    async def generate():
        for chunk in range(10):
            test_token = f"Token {chunk}"
            logger.info(f"Streaming response test yielding token: {test_token}")
            yield f"Data {chunk}\n"
            await asyncio.sleep(1)  # simulate some delay

    return StreamingResponse(generate(), media_type="text/plain")


@app.post(VOICE_TO_TEXT_ENDPOINT, response_model=VoiceToTextResponse)
async def voice_to_text(request: VoiceToTextRequest) -> VoiceToTextResponse:
    transcript_text = await transcribe_audio(
        request.audio_file_url,
        prompt=request.prompt,
        response_format=request.response_format,
        temperature=request.temperature,
        language=request.language
    )
    return VoiceToTextResponse(text=transcript_text)


@app.post(DATABASE_UPSERT_ENDPOINT, response_model=DatabaseUpsertResponse)
async def database_upsert(database_upsert_request: DatabaseUpsertRequest) -> DatabaseUpsertResponse:
    logger.info(f"Upserting data into database query - {database_upsert_request.query}")
    mongo_database = await get_or_create_mongo_database_manager()
    success = await mongo_database.upsert(**database_upsert_request.dict())
    if success:
        return DatabaseUpsertResponse(success=True)
    else:
        return DatabaseUpsertResponse(success=False)


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
        f"Server: {server} - {server.config} - {server.config.app} - Started on {server.config.host}:{server.config.port}")
    await server.serve()


def run_api_sync():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_api_async())


if __name__ == '__main__':
    asyncio.run(run_api_async())

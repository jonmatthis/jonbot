import asyncio
import logging
from typing import AsyncIterable, Awaitable

from fastapi import FastAPI
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from starlette.responses import StreamingResponse

from jonbot.layer1_api_interface.endpoints.chat import chat
from jonbot.layer1_api_interface.endpoints.database import database_upsert
from jonbot.layer2_core_processes.audio_transcription.transcribe_audio import transcribe_audio
from jonbot.layer2_core_processes.utilities.generate_test_tokens import generate_test_tokens
from jonbot.layer3_data_layer.database.get_or_create_mongo_database_manager import get_or_create_mongo_database_manager
from jonbot.models.conversation_models import ChatResponse, ChatRequest
from jonbot.models.database_upsert_models import DatabaseUpsertResponse, DatabaseUpsertRequest
from jonbot.models.health_check_status import HealthCheckResponse
from jonbot.models.voice_to_text_request import VoiceToTextResponse, VoiceToTextRequest
from scratchpad.api_streaming_test.fastapi_langchain_streaming_test_app import send_message

logger = logging.getLogger(__name__)

HEALTH_ENDPOINT = "/health"
CHAT_ENDPOINT = "/chat"
CHAT_STREAM_ENDPOINT = "/chat_stream"
STREAMING_RESPONSE_TEST_ENDPOINT = "/test_streaming_response"
VOICE_TO_TEXT_ENDPOINT = "/voice_to_text"
DATABASE_UPSERT_ENDPOINT = "/database_upsert"

APP = None


def get_or_create_fastapi_app():
    global APP
    if APP is None:
        APP = FastAPI()
    return APP


app = get_or_create_fastapi_app()


@app.on_event("startup")
async def startup_event():
    logger.info("Starting up...")
    logger.info("Creating MongoDatabaseManager instance")
    await get_or_create_mongo_database_manager()
    logger.info("Startup complete!")


@app.get(HEALTH_ENDPOINT, response_model=HealthCheckResponse)
async def health_check_endpoint():
    return HealthCheckResponse(status="alive")


@app.post(STREAMING_RESPONSE_TEST_ENDPOINT)
async def streaming_response_test_endpoint():
    return StreamingResponse(generate_test_tokens(), media_type="text/plain")


@app.post(VOICE_TO_TEXT_ENDPOINT, response_model=VoiceToTextResponse)
async def voice_to_text_endpoint(voice_to_text_request: VoiceToTextRequest) -> VoiceToTextResponse:
    transcript_text = await transcribe_audio(**voice_to_text_request.dict())
    return VoiceToTextResponse(text=transcript_text)


# @app.post(CHAT_STREAM_ENDPOINT)
# async def chat_stream_endpoint(chat_request: ChatRequest, response_model=None) -> StreamingResponse:
#     return await chat_stream(chat_request=chat_request)
@app.post(CHAT_STREAM_ENDPOINT)
async def chat_stream_endpoint(chat_request: ChatRequest):
    logger.info(f"Received chat stream request: {chat_request}")
    return StreamingResponse(stream_chat(chat_request), media_type="text/event-stream")

async def stream_chat(chat_request: ChatRequest) -> AsyncIterable[str]:
    callback = AsyncIteratorCallbackHandler()
    model = ChatOpenAI(
        streaming=True,
        verbose=True,
        callbacks=[callback],
    )

    async def wrap_done(awaitable_function: Awaitable, event: asyncio.Event):
        """Wrap an awaitable with a event to signal when it's done or an exception is raised."""
        try:
            await awaitable_function
        except Exception as e:
            # TODO: handle exception
            print(f"Caught exception: {e}")
        finally:
            # Signal the aiter to stop.
            event.set()

    # Begin a task that runs in the background.
    task = asyncio.create_task(wrap_done(
        model.agenerate(messages=[[HumanMessage(content=chat_request.chat_input.message)]]),
        callback.done),
    )

    async for token in callback.aiter():
        # Use server-sent-events to stream the response
        yield f"data: {token}\n\n"

    await task



@app.post(CHAT_ENDPOINT, response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatRequest) -> ChatResponse:
    logger.info(f"Received chat request: {chat_request}")
    return await chat(chat_request=chat_request)


@app.post(DATABASE_UPSERT_ENDPOINT, response_model=DatabaseUpsertResponse)
async def database_upsert_endpoint(database_upsert_request: DatabaseUpsertRequest) -> DatabaseUpsertResponse:
    return await database_upsert(database_upsert_request=database_upsert_request)

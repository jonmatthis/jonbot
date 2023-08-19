from fastapi import FastAPI
from starlette.responses import StreamingResponse

from jonbot import get_logger
from jonbot.layer2_core_processes.core.ai.components.memory.construct_memory_data import \
    calculate_memory_from_context_route
from jonbot.layer2_core_processes.core.audio_transcription import transcribe_audio
from jonbot.layer2_core_processes.entrypoint_functions.chat_stream import chat_stream_function
from jonbot.layer2_core_processes.entrypoint_functions.database_actions import database_upsert, \
    get_message_history_document
from jonbot.layer2_core_processes.utilities.generate_test_tokens import generate_test_tokens
from jonbot.layer3_data_layer.database.get_or_create_mongo_database_manager import get_or_create_mongo_database_manager
from jonbot.models.calculate_memory_request import CalculateMemoryRequest
from jonbot.models.conversation_models import ChatResponse, ChatRequest, MessageHistory
from jonbot.models.database_request_response_models import DatabaseUpsertResponse, DatabaseUpsertRequest, \
    MessageHistoryRequest
from jonbot.models.health_check_status import HealthCheckResponse
from jonbot.models.voice_to_text_request import VoiceToTextResponse, VoiceToTextRequest

logger = get_logger()

HEALTH_ENDPOINT = "/health"
CHAT_ENDPOINT = "/chat"
CHAT_STREAM_ENDPOINT = "/chat_stream"
STREAMING_RESPONSE_TEST_ENDPOINT = "/test_streaming_response"
VOICE_TO_TEXT_ENDPOINT = "/voice_to_text"

DATABASE_UPSERT_ENDPOINT = "/database_upsert"
MESSAGE_HISTORY_ENDPOINT = "/message_history"
CALCULATE_MEMORY_ENDPOINT = "/calculate_memory"

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
    return StreamingResponse(chat_stream_function(chat_request), media_type="text/event-stream")


@app.post(CHAT_ENDPOINT, response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatRequest) -> ChatResponse:
    logger.error("Not implemented yet! Use the chat_stream endpoint instead.")
    raise NotImplementedError("Not implemented yet!")


@app.post(DATABASE_UPSERT_ENDPOINT, response_model=DatabaseUpsertResponse)
async def database_upsert_endpoint(database_upsert_request: DatabaseUpsertRequest) -> DatabaseUpsertResponse:
    return await database_upsert(database_upsert_request=database_upsert_request)


@app.post(MESSAGE_HISTORY_ENDPOINT, response_model=MessageHistory)
async def message_history_endpoint(message_history_request: MessageHistoryRequest) -> MessageHistory:
    return await get_message_history_document(message_history_request=message_history_request)


@app.post(CALCULATE_MEMORY_ENDPOINT)
async def calculate_memory_endpoint(calculate_memory_request: CalculateMemoryRequest) -> bool:
    return await calculate_memory_from_context_route(**calculate_memory_request.dict())

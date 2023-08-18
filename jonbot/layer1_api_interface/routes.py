import asyncio

from fastapi import FastAPI
from starlette.responses import StreamingResponse

from jonbot import get_logger
from jonbot.layer2_core_processes.entrypoint_functions.chat import chat
from jonbot.layer2_core_processes.entrypoint_functions.chat_stream import chat_stream_function
from jonbot.layer2_core_processes.entrypoint_functions.database_actions import database_upsert, get_conversation_history
from jonbot.layer2_core_processes.core.audio_transcription import transcribe_audio
from jonbot.layer2_core_processes.utilities.generate_test_tokens import generate_test_tokens
from jonbot.layer3_data_layer.database.get_or_create_mongo_database_manager import get_or_create_mongo_database_manager
from jonbot.models.conversation_models import ChatResponse, ChatRequest, ConversationHistory
from jonbot.models.database_request_response_models import DatabaseUpsertResponse, DatabaseUpsertRequest, \
    ConversationHistoryRequest
from jonbot.models.health_check_status import HealthCheckResponse
from jonbot.models.voice_to_text_request import VoiceToTextResponse, VoiceToTextRequest

logger = get_logger()

HEALTH_ENDPOINT = "/health"
CHAT_ENDPOINT = "/chat"
CHAT_STREAM_ENDPOINT = "/chat_stream"
STREAMING_RESPONSE_TEST_ENDPOINT = "/test_streaming_response"
VOICE_TO_TEXT_ENDPOINT = "/voice_to_text"

DATABASE_UPSERT_ENDPOINT = "/database_upsert"
CONVERSATION_HISTORY_ENDPOINT = "/conversation_history"


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
    logger.info(f"Received chat request: {chat_request}")
    return await chat(chat_request=chat_request)


@app.post(DATABASE_UPSERT_ENDPOINT, response_model=DatabaseUpsertResponse)
async def database_upsert_endpoint(database_upsert_request: DatabaseUpsertRequest) -> DatabaseUpsertResponse:
    return await database_upsert(database_upsert_request=database_upsert_request)


@app.post(CONVERSATION_HISTORY_ENDPOINT, response_model=ConversationHistory)
async def conversation_history_endpoint(conversation_history_request: ConversationHistoryRequest) -> ConversationHistory:
    return await get_conversation_history(conversation_history_request=conversation_history_request)

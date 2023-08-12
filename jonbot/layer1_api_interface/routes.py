import logging

from fastapi import FastAPI
from starlette.responses import StreamingResponse

from jonbot.layer1_api_interface.endpoints.chat_stream import chat_stream
from jonbot.layer1_api_interface.endpoints.database import database_upsert
from jonbot.layer2_core_processes.audio_transcription.transcribe_audio import transcribe_audio
from jonbot.layer2_core_processes.utilities.generate_test_tokens import generate_test_tokens
from jonbot.models import ChatRequest, ChatResponse
from jonbot.models import DatabaseUpsertResponse, DatabaseUpsertRequest
from jonbot.models import HealthCheckResponse
from jonbot.models.voice_to_text_request import VoiceToTextResponse, VoiceToTextRequest
from jonbot.layer3_data_layer.database.get_or_create_mongo_database_manager import get_or_create_mongo_database_manager

logger = logging.getLogger(__name__)

HEALTH_ENDPOINT = "/health"
CHAT_ENDPOINT = "/chat"
CHAT_STREAM_ENDPOINT = "/chat_stream"
STREAMING_RESPONSE_TEST_ENDPOINT = "/test_streaming_response"
VOICE_TO_TEXT_ENDPOINT = "/voice_to_text"
DATABASE_UPSERT_ENDPOINT = "/database_upsert"

app = FastAPI()


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


@app.post(CHAT_STREAM_ENDPOINT, response_model=StreamingResponse)
async def chat_stream_endpoint(chat_request: ChatRequest) -> StreamingResponse:
    return await chat_stream(chat_request=chat_request)


@app.post(CHAT_ENDPOINT, response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatRequest) -> ChatResponse:
    return await chat_stream(chat_request=chat_request)


@app.post(DATABASE_UPSERT_ENDPOINT, response_model=DatabaseUpsertResponse)
def database_upsert_endpoint(database_upsert_request: DatabaseUpsertRequest) -> DatabaseUpsertResponse:
    return database_upsert(database_upsert_request=database_upsert_request)

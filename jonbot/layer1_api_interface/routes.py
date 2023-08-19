from fastapi import FastAPI
from starlette.responses import StreamingResponse

from jonbot import get_logger
from jonbot.layer2_core_processes.core.ai.components.memory.memory_data_calculator import \
    calculate_memory_from_context_route
from jonbot.layer2_core_processes.core.audio_transcription import transcribe_audio
from jonbot.layer2_core_processes.chatbot_function import chatbot_function
from jonbot.layer2_core_processes.backend_database_actions import upsert_discord_message, \
    get_message_history_document
from jonbot.layer2_core_processes.utilities.generate_test_tokens import generate_test_tokens
from jonbot.layer3_data_layer.database.get_or_create_mongo_database_manager import get_or_create_mongo_database_manager
from jonbot.models.calculate_memory_request import CalculateMemoryRequest
from jonbot.models.context_memory_document import ContextMemoryDocument
from jonbot.models.conversation_models import ChatResponse, ChatRequest, MessageHistory
from jonbot.models.database_request_response_models import LogDiscordMessageResponse, MessageHistoryRequest, UpsertDiscordMessageRequest
from jonbot.models.health_check_status import HealthCheckResponse
from jonbot.models.voice_to_text_request import VoiceToTextResponse, VoiceToTextRequest

logger = get_logger()

HEALTH_ENDPOINT = "/health"

CHAT_ENDPOINT = "/chat"
STREAMING_RESPONSE_TEST_ENDPOINT = "/test_streaming_response"
VOICE_TO_TEXT_ENDPOINT = "/voice_to_text"

UPSERT_MESSAGE_ENDPOINT = "/upsert_message"
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



@app.post(CHAT_ENDPOINT)
async def chat_endpoint(chat_request: ChatRequest):
    logger.info(f"Received chat request: {chat_request}")
    return StreamingResponse(chatbot_function(chat_request), media_type="text/event-stream")


@app.post(UPSERT_MESSAGE_ENDPOINT)
async def upsert_message_endpoint(log_discord_message_request: UpsertDiscordMessageRequest) -> LogDiscordMessageResponse:
    return await upsert_discord_message(upsert_discord_message_request=log_discord_message_request)


@app.post(MESSAGE_HISTORY_ENDPOINT, response_model=MessageHistory)
async def message_history_endpoint(message_history_request: MessageHistoryRequest) -> MessageHistory:
    return await get_message_history_document(message_history_request=message_history_request)


@app.post(CALCULATE_MEMORY_ENDPOINT, response_model=ContextMemoryDocument)
async def calculate_memory_endpoint(calculate_memory_request: CalculateMemoryRequest) -> ContextMemoryDocument:
    response =  await calculate_memory_from_context_route(**calculate_memory_request.dict())
    return response

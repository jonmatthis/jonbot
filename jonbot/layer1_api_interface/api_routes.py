from fastapi import FastAPI
from starlette.responses import StreamingResponse

from jonbot import get_jonbot_logger
from jonbot.layer2_processing.backend_database_operator.backend_database_operator import (
    BackendDatabaseOperations,
)
from jonbot.layer2_processing.controller.controller import Controller
from jonbot.models.calculate_memory_request import CalculateMemoryRequest
from jonbot.models.context_memory_document import ContextMemoryDocument
from jonbot.models.conversation_models import ChatRequest
from jonbot.models.database_request_response_models import (
    UpsertDiscordMessagesResponse,
    UpsertDiscordMessagesRequest,
)
from jonbot.models.health_check_status import HealthCheckResponse
from jonbot.models.voice_to_text_request import VoiceToTextResponse, VoiceToTextRequest

logger = get_jonbot_logger()

HEALTH_ENDPOINT = "/health"

CHAT_ENDPOINT = "/chat"
VOICE_TO_TEXT_ENDPOINT = "/voice_to_text"

UPSERT_MESSAGES_ENDPOINT = "/upsert_message"
CALCULATE_MEMORY_ENDPOINT = "/calculate_memory"


def register_api_routes(
    app: FastAPI,
        database_operations: BackendDatabaseOperations,
        controller: Controller
):
    @app.get(HEALTH_ENDPOINT, response_model=HealthCheckResponse)
    async def health_check_endpoint():
        return HealthCheckResponse(status="alive")

    @app.post(VOICE_TO_TEXT_ENDPOINT, response_model=VoiceToTextResponse)
    async def voice_to_text_endpoint(
        voice_to_text_request: VoiceToTextRequest,
    ) -> VoiceToTextResponse:
        response = await controller.transcribe_audio(
            voice_to_text_request=voice_to_text_request
        )
        if response is None:
            return VoiceToTextResponse(success=False)
        return response

    @app.post(CALCULATE_MEMORY_ENDPOINT, response_model=ContextMemoryDocument)
    async def calculate_memory_endpoint(
        calculate_memory_request: CalculateMemoryRequest,
    ) -> ContextMemoryDocument:
        response = await controller.calculate_memory(calculate_memory_request)
        return response

    @app.post(CHAT_ENDPOINT)
    async def chat_endpoint(chat_request: ChatRequest):
        logger.info(f"Received chat request: {chat_request}")
        return StreamingResponse(
            controller.get_response_from_chatbot(chat_request=chat_request),
            media_type="text/event-stream",
        )

    @app.post(UPSERT_MESSAGES_ENDPOINT)
    async def upsert_messages_endpoint(
        request: UpsertDiscordMessagesRequest,
    ) -> UpsertDiscordMessagesResponse:
        return await database_operations.upsert_discord_messages(request=request)

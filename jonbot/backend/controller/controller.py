from typing import AsyncIterable, Dict

from jonbot.backend.ai.audio_transcription.transcribe_audio import transcribe_audio
from jonbot.backend.ai.chatbot.chatbot import (
    Chatbot,
)
from jonbot.backend.ai.chatbot.get_chatbot import (
    get_chatbot,
)
from jonbot.backend.backend_database_operator.backend_database_operator import (
    BackendDatabaseOperations,
)
from jonbot.backend.data_layer.models.conversation_models import ChatRequest
from jonbot.backend.data_layer.models.voice_to_text_request import VoiceToTextRequest, VoiceToTextResponse
from jonbot.system.setup_logging.get_logger import get_jonbot_logger

logger = get_jonbot_logger()


class Controller:
    def __init__(self, database_operations: BackendDatabaseOperations):
        self.database_operations = database_operations
        self.chatbots: Dict[str, Chatbot] = {}

    @staticmethod
    async def transcribe_audio(
            voice_to_text_request: VoiceToTextRequest,
    ) -> VoiceToTextResponse:
        response = await transcribe_audio(**voice_to_text_request.dict())
        if response is None:
            raise Exception(f"Transcription failed for audio: {voice_to_text_request}")
        return response

    async def get_response_from_chatbot(
            self, chat_request: ChatRequest
    ) -> AsyncIterable[str]:
        logger.info(f"Received chat stream request: {chat_request}")
        chatbot = await get_chatbot(
            chat_request=chat_request,
            existing_chatbots=self.chatbots,
            database_operations=self.database_operations,
        )

        logger.debug(f"Grabbed chatbot: {chatbot}")
        async for response in chatbot.execute(
                message_string=chat_request.chat_input.message,
                message_id=chat_request.message_id,
                reply_message_id=chat_request.reply_message_id,
        ):
            logger.trace(f"Yielding response: {response}")
            yield response

        logger.info(f"Chat stream request complete: {chat_request}")

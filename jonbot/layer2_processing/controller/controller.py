from typing import AsyncIterable, Optional

from jonbot import get_logger
from jonbot.layer2_processing.ai.audio_transcription.transcribe_audio import (
    transcribe_audio_function,
)
from jonbot.layer2_processing.ai.chatbot.chatbot_handler import ChatbotHandler
from jonbot.layer2_processing.backend_database_operator.backend_database_operator import (
    BackendDatabaseOperations,
)
from jonbot.models.calculate_memory_request import CalculateMemoryRequest
from jonbot.models.context_memory_document import ContextMemoryDocument
from jonbot.models.conversation_models import ChatRequest
from jonbot.models.voice_to_text_request import VoiceToTextRequest, VoiceToTextResponse

logger = get_logger()


class Controller:
    def __init__(self, database_operations: BackendDatabaseOperations):
        self.database_operations = database_operations
        self.chatbot_handler = ChatbotHandler(database_operations=database_operations)

    @staticmethod
    async def transcribe_audio(
        voice_to_text_request: VoiceToTextRequest,
    ) -> VoiceToTextResponse:
        response = await transcribe_audio_function(**voice_to_text_request.dict())
        if response is None:
            raise Exception(f"Transcription failed for audio: {voice_to_text_request}")
        return response

    async def get_response_from_chatbot(
        self, chat_request: ChatRequest
    ) -> AsyncIterable[str]:
        logger.info(f"Received chat stream request: {chat_request}")
        chatbot = await self.chatbot_handler.get_chatbot(chat_request=chat_request)
        async for response in chatbot.execute(
            message_string=chat_request.chat_input.message
        ):
            logger.trace(f"BACKEND (CONTROLLER) - Yielding response: {response}")
            yield response

        logger.info(f"Chat stream request complete: {chat_request}")

    async def calculate_memory(
        self, calculate_memory_request: CalculateMemoryRequest
    ) -> Optional[ContextMemoryDocument]:
        pass
        # try:
        #     memory_calculator = await MemoryDataCalculator.from_calculate_memory_request(
        #         calculate_memory_request=calculate_memory_request,
        #         database_operations=self.database_operations)
        #
        #     if memory_calculator is None:
        #         logger.exception(
        #             f"`MemoryCalculator` returned  `None` for context route: {calculate_memory_request.context_route.as_flat_dict}")
        #         return
        #     else:
        #         context_memory_document = await memory_calculator.calculate(upsert=True)
        # except Exception as e:
        #     logger.error(
        #         f"Error occurred while calculating memory from context route: {calculate_memory_request.context_route.as_flat_dict}. Error: {e}")
        #     raise
        #
        # return context_memory_document

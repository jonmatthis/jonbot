from typing import AsyncIterable, Dict, Optional

from jonbot.backend.ai.audio_transcription.transcribe_audio import (
    transcribe_audio_function,
)
from jonbot.backend.ai.chatbot.chatbot import (
    ChatbotLLMChain,
)
from jonbot.backend.ai.chatbot.get_chatbot import (
    get_chatbot,
)
from jonbot.backend.backend_database_operator.backend_database_operator import (
    BackendDatabaseOperations,
)
from jonbot.backend.data_layer.models.calculate_memory_request import CalculateMemoryRequest
from jonbot.backend.data_layer.models.context_memory_document import ContextMemoryDocument
from jonbot.backend.data_layer.models.conversation_models import ChatRequest
from jonbot.backend.data_layer.models.database_request_response_models import ContextMemoryDocumentRequest
from jonbot.backend.data_layer.models.voice_to_text_request import VoiceToTextRequest, VoiceToTextResponse
from jonbot.system.setup_logging.get_logger import get_jonbot_logger

logger = get_jonbot_logger()


class Controller:
    def __init__(self, database_operations: BackendDatabaseOperations):
        self.database_operations = database_operations
        self.chatbots: Dict[str, ChatbotLLMChain] = {}

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

    async def get_context_memory(
            self,
            context_memory_request: ContextMemoryDocumentRequest
    ) -> Optional[ContextMemoryDocument]:
        logger.info(
            f"Loading context memory for context route: {self.context_route.dict()} from database: {self.database_name}..."
        )
        get_request = ContextMemoryDocumentRequest.build_get_request(
            context_route=self.context_route,
            summary_prompt=self.summary_prompt,
            database_name=self.database_name,
        )
        response = await self.database_operations.get_context_memory_document(
            request=get_request
        )

        if not response.success:
            logger.warning(
                f"Could not load context memory from database for context route: {get_request.query}"
            )
            return

        return response.data

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

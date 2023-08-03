import logging

from jonbot.layer2_core_processes.processing_sublayer.ai.chatbot.chatbot import Chatbot
from jonbot.layer3_data_layer.data_models.conversation_models import ChatInput, ChatResponse

logger = logging.getLogger(__name__)


class AIResponseHandler:

    async def init_chatbot(self):
        self.chatbot = await Chatbot().create_chatbot()

    async def get_chat_response(self, chat_input: ChatInput) -> ChatResponse:
        return await self.chatbot.get_chat_response(chat_input=chat_input)

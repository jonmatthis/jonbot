import logging

from pydantic import BaseModel

from jonbot.layer2_core_processes.processing_sublayer.ai.chatbot.chatbot import Chatbot
from jonbot.layer3_data_layer.data_models.conversation_models import ChatInput

logger = logging.getLogger(__name__)

class AIResponseHandler(BaseModel):
    chatbot = Chatbot()

    async def get_chat_response(self, chat_input: ChatInput):
        return await self.chatbot.get_chat_response(chat_input=chat_input)


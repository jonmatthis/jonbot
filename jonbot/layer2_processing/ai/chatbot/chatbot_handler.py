from typing import Dict

from pydantic import BaseModel

from jonbot import get_logger
from jonbot.layer2_processing.ai.chatbot.chatbot import (
    Chatbot,
)
from jonbot.layer2_processing.ai.chatbot.components.memory.memory_handler import (
    MemoryHandler,
)
from jonbot.layer2_processing.backend_database_operator.backend_database_operator import (
    BackendDatabaseOperations,
)
from jonbot.models.conversation_models import ChatRequest

logger = get_logger()


class ChatbotHandler(BaseModel):
    database_operations: BackendDatabaseOperations
    chatbots: Dict[str, Chatbot] = {}

    class Config:
        arbitrary_types_allowed = True

    async def get_chatbot(self, chat_request: ChatRequest) -> Chatbot:
        context_path = str(chat_request.context_route.as_flat_dict)

        if context_path in self.chatbots:
            logger.debug(
                f"Found chatbot: {self.chatbots[context_path]} for context path: {context_path}"
            )
            return self.chatbots[context_path]
        else:
            self.chatbots[context_path] = await self._create_chatbot(
                chat_request=chat_request
            )
            logger.debug(
                f"Created chatbot: {self.chatbots[context_path]} for context path: {context_path}"
            )
            return self.chatbots[context_path]

    async def _create_chatbot(
        self,
        chat_request: ChatRequest,
    ) -> Chatbot:
        memory_handler = await MemoryHandler.from_chat_request(
            chat_request=chat_request,
            database_operations=self.database_operations,
        )
        chatbot = await Chatbot.from_memory_handler(memory_handler=memory_handler)

        return chatbot

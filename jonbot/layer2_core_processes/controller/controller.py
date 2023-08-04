import logging
import uuid
from typing import Optional

from pydantic import Field, BaseModel

from jonbot.layer2_core_processes.processing_sublayer.ai_nlp_llm_stuff.ai_response_handler import (
    AIResponseHandler,
)
from jonbot.layer3_data_layer.data_models.conversation_models import (
    ChatInput,
    ChatResponse,
    ChatInteraction,
)

logger = logging.getLogger(__name__)



class Controller(BaseModel):
    """
    Handles communication with the API layer, gets data from the database, sends `request+ parameters + data`
    to `processing` sublayer, and then returns results to the API and database layers.
    """

    ai_response_handler: AIResponseHandler = Field(default_factory=AIResponseHandler)

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    async def initialize(cls, *args, **kwargs):
        self = Controller(*args, **kwargs)
        await self.ai_response_handler.init_chatbot()
        return self

    async def handle_chat_input(self, chat_input: ChatInput) -> ChatResponse:
        """
        Process the chat input

        Args:
            user_message (str): Message input by user

        Returns:
            ChatResponse: Response to user input
        """
        logger.info(f"Received chat input: {chat_input.message}")

        # Perform any necessary processing on the chat input
        bot_response = await self.ai_response_handler.get_chat_response(chat_input)

        logger.info(f"Returning chat response: {bot_response.message}")

        return bot_response

import logging
import uuid
from typing import Optional

from pydantic import Field, BaseModel

from jonbot.layer2_core_processes.processing_sublayer.get_bot_response import (
    get_bot_response,
)
from jonbot.layer3_data_layer.data_models.conversation_models import (
    ChatInput,
    ChatResponse,
    ChatInteraction,
    Timestamp,
)
from jonbot.layer3_data_layer.database.abstract_database import AbstractDatabase
from jonbot.layer3_data_layer.database.mongo_database import MongoDatabase

logger = logging.getLogger(__name__)


def create_database() -> AbstractDatabase:
    """Factory function to create a MongoDatabase instance."""
    logger.info("Creating MongoDatabase instance")
    return MongoDatabase()


class Controller(BaseModel):
    """
    Handles communication with the API layer, gets data from the database, sends `request+ parameters + data`
    to `processing` sublayer, and then returns results to the API and database layers.
    """

    database: Optional[AbstractDatabase] = Field(default_factory=create_database)
    conversation_id: str = str(uuid.uuid4())
    user_id: str = str(uuid.uuid4())
    logger.info(f"Created controller with conversation_id: {conversation_id}, user_id: {user_id}")

    class Config:
        arbitrary_types_allowed = True

    def handle_chat_input(self, chat_input: ChatInput) -> ChatResponse:
        """
        Process the chat input

        Args:
            user_message (str): Message input by user

        Returns:
            ChatResponse: Response to user input
        """
        logger.info(f"Received chat input: {chat_input}")
        # Log user and conversation
        self.database.log_user(self.user_id)
        self.database.log_conversation(conversation_id=self.conversation_id)

        # Perform any necessary processing on the chat input
        response_message = get_bot_response(chat_input=chat_input)
        bot_response = ChatResponse(
            message=response_message,
            metadata={
                "conversation_id": self.conversation_id,
                "user_id": self.user_id,
                "timestamp": Timestamp().model_dump(),
            },
        )
        logger.info(f"Returning chat response: {bot_response}")
        chat_interaction = ChatInteraction(
            human_input=chat_input,
            bot_response=bot_response,
        )
        self.database.add_interaction_to_conversation(
            conversation_id=self.conversation_id,
            interaction=chat_interaction,
        )
        return bot_response

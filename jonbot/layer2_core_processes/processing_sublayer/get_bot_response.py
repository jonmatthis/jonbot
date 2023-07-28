import logging

from jonbot.layer3_data_layer.data_models.conversation_models import ChatInput

logger = logging.getLogger(__name__)


def get_bot_response(chat_input: ChatInput) -> str:
    logger.info(f"Received chat input: {chat_input.message}")
    return f"I heard you say:  \n '{chat_input.message}'\n"

from jonbot.layer3_data_layer.data_models.conversation_models import ChatInput

import logging
logger = logging.getLogger(__name__)

def get_bot_response(chat_input: ChatInput) -> str:
    logger.info(f"Received chat input: {chat_input}")
    return f"I heard you say:  \n '{chat_input}'\n"
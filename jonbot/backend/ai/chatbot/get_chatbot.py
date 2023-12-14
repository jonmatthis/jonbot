from typing import Dict

from jonbot.backend.ai.chatbot.chatbot import (
    Chatbot,
)
from jonbot.backend.backend_database_operator.backend_database_operator import (
    BackendDatabaseOperations,
)
from jonbot.backend.data_layer.models.conversation_models import ChatRequest
from jonbot.system.setup_logging.get_logger import get_jonbot_logger

logger = get_jonbot_logger()


async def get_chatbot(
        chat_request: ChatRequest,
        existing_chatbots: Dict[str, Chatbot],
        database_operations: BackendDatabaseOperations,
) -> Chatbot:
    context_path = str(chat_request.context_route.as_flat_dict)

    if not context_path in existing_chatbots.keys():
        existing_chatbots[context_path] = await Chatbot.from_chat_request(
            chat_request=chat_request,
            database_operations=database_operations,
        )

    chatbot = existing_chatbots[context_path]
    await chatbot.apply_config_and_build_chain(config=chat_request.config)

    return chatbot

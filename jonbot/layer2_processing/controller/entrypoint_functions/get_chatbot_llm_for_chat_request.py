from typing import Dict

from jonbot import get_logger
from jonbot.layer2_processing.controller.entrypoint_functions.backend_database_operations import \
    BackendDatabaseOperations
from jonbot.layer2_processing.core_processing.ai.chatbot_llm_chain.chatbot_llm_chain import ChatbotLLMChain
from jonbot.models.conversation_models import ChatRequest

logger = get_logger()


async def get_chatbot_llm_chain_for_chat_request(chat_request: ChatRequest,
                                                 existing_chatbot_llm_chains: Dict[str, ChatbotLLMChain],
                                                 database_operations: BackendDatabaseOperations) -> ChatbotLLMChain:
    context_path = str(chat_request.context_route.as_query)

    if context_path in existing_chatbot_llm_chains:
        return existing_chatbot_llm_chains[context_path]
    else:
        existing_chatbot_llm_chains[context_path] = await ChatbotLLMChain.from_context_route(
            context_route=chat_request.context_route,
            database_name=chat_request.database_name,
            database_operations=database_operations,
        )
        return existing_chatbot_llm_chains[context_path]

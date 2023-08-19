from typing import Dict

from jonbot import get_logger
from jonbot.layer2_core_processes.core.ai.chatbot_llm_chain.chatbot_llm_chain import ChatbotLLMChain
from jonbot.models.conversation_models import ChatRequest

logger = get_logger()

chatbot_llm_chains: Dict[str, ChatbotLLMChain] = {}


async def get_chatbot_llm_chain_for_chat_request(chat_request: ChatRequest) -> ChatbotLLMChain:
    global chatbot_llm_chains
    context_path = chat_request.context_route.as_path

    if context_path in chatbot_llm_chains:
        return chatbot_llm_chains[context_path]
    else:
        chatbot_llm_chains[context_path] = await ChatbotLLMChain.from_context_route(
            context_route=chat_request.context_route,
            database_name=chat_request.database_name
            )
        return chatbot_llm_chains[context_path]

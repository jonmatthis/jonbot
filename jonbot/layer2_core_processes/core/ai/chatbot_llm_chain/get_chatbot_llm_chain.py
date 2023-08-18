from typing import Dict

from jonbot import get_logger
from jonbot.layer2_core_processes.entrypoint_functions.database_actions import \
    get_conversation_history_from_chat_request
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
        conversation_history = await get_conversation_history_from_chat_request(chat_request=chat_request)
        chatbot_llm_chains[context_path] = ChatbotLLMChain(conversation_history=conversation_history)
        return chatbot_llm_chains[context_path]



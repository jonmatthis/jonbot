from typing import Dict

from jonbot import get_logger
from jonbot.layer2_core_processes.entrypoint_functions.database_actions import \
    get_conversation_history_from_chat_request
from jonbot.layer2_core_processes.core.ai.expression_langchain.chatbot_llm_chain import LLMChatChain
from jonbot.models.conversation_models import ChatRequest

logger = get_logger()

active_chats: Dict[str, LLMChatChain] = {}


async def get_llm_chain_for_chat_request(chat_request: ChatRequest) -> LLMChatChain:
    global active_chats
    context_path = chat_request.context_route.as_path

    if context_path in active_chats:
        return active_chats[context_path]
    else:
        conversation_history = await get_conversation_history_from_chat_request(chat_request=chat_request)
        active_chats[context_path] = LLMChatChain(conversation_history=conversation_history)
        return active_chats[context_path]



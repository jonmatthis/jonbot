from typing import Dict

from jonbot import get_logger
from jonbot.layer1_api_interface.endpoints.database_actions import get_conversation_history
from jonbot.layer2_core_processes.ai_chatbot.expression_langchain.llm_chat_chain import LLMChatChain
from jonbot.models.conversation_models import ChatRequest
from jonbot.models.database_request_response_models import ConversationHistoryRequest

logger = get_logger()

active_chats: Dict[str, LLMChatChain] = {}


async def get_llm_chain_for_chat_request(chat_request: ChatRequest) -> LLMChatChain:
    global active_chats
    context_path = chat_request.context_route.as_path

    if context_path in active_chats:
        return active_chats[context_path]
    else:
        conversation_history_request = ConversationHistoryRequest(database_name=chat_request.database_name,
                                                                  context_route=chat_request.context_route)
        conversation_history = await get_conversation_history(conversation_history_request=conversation_history_request)
        active_chats[context_path] = LLMChatChain(conversation_history=conversation_history)
        return active_chats[context_path]

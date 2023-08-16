from jonbot import get_logger
from jonbot.layer2_core_processes.ai_chatbot.expression_langchain.llm_chat_chain import LLMChatChain
from jonbot.models.conversation_models import ChatRequest

logger = get_logger()

active_chats = {}

def get_llm_chain_for_chat_request(chat_request: ChatRequest) -> LLMChatChain:
    global active_chats
    context_route = chat_request.conversation_context.context_route.parent
    if context_route in active_chats:
        return active_chats[context_route]
    else:
        active_chats[context_route] = LLMChatChain(message=chat_request.chat_input.message)
        return active_chats[context_route]

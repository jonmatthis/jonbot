from typing import AsyncIterable

from jonbot.layer2_core_processes.ai_chatbot.expression_langchain.get_llm_chat_chain import \
    get_llm_chain_for_chat_request
from jonbot.layer2_core_processes.ai_chatbot.expression_langchain.llm_chat_chain import LLMChatChain
from jonbot.models.conversation_models import ChatRequest


async def chat_stream_function(chat_request: ChatRequest) -> AsyncIterable[str]:
    llm_chain = get_llm_chain_for_chat_request(chat_request)
    async for response in llm_chain.execute(message_string=chat_request.chat_input.message):
        yield response



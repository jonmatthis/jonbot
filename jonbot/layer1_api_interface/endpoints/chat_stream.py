from typing import AsyncIterable

from jonbot import get_logger
from jonbot.layer2_core_processes.ai_chatbot.expression_langchain.get_llm_chat_chain import \
    get_llm_chain_for_chat_request
from jonbot.models.conversation_models import ChatRequest

logger = get_logger()

async def chat_stream_function(chat_request: ChatRequest) -> AsyncIterable[str]:
    logger.info(f"Received chat stream request: {chat_request}")
    llm_chain = get_llm_chain_for_chat_request(chat_request)
    async for response in llm_chain.execute(message_string=chat_request.chat_input.message):
        yield response



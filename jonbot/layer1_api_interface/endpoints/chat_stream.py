import logging

from starlette.responses import StreamingResponse

from jonbot.layer2_core_processes.ai_chatbot.ai_chatbot import AIChatBot
from jonbot.layer2_core_processes.ai_chatbot.components.callbacks.callbacks import StreamingAsyncCallbackHandler
from jonbot.layer3_data_layer.database.get_or_create_mongo_database_manager import get_or_create_mongo_database_manager
from jonbot.models.conversation_models import ChatRequest

logger = logging.getLogger(__name__)


async def chat_stream(chat_request: ChatRequest):
    logger.info(f"Received chat_stream request: {chat_request}")

    mongo_database = await get_or_create_mongo_database_manager()
    conversation_history = await mongo_database.get_conversation_history(
        context_route=chat_request.conversation_context.context_route)

    ai_chat_bot = await AIChatBot.build(conversation_context=chat_request.conversation_context,
                                        conversation_history=conversation_history, )

    ai_chat_bot.add_callback_handler(handler=StreamingAsyncCallbackHandler())

    async def stream_response():
        async for token in ai_chat_bot.stream_chat_response_tokens(input_text=chat_request.chat_input.message):
            logger.debug(f"Streaming token: {token['text']}")
            yield token["text"]

    return StreamingResponse(stream_response(), media_type="text/plain")

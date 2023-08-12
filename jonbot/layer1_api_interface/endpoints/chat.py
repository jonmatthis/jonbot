from langchain.callbacks import StreamingStdOutCallbackHandler

from jonbot.layer2_core_processes.ai_chatbot.ai_chatbot import AIChatBot

from langchain.callbacks import StreamingStdOutCallbackHandler

from jonbot.layer2_core_processes.ai_chatbot.ai_chatbot import AIChatBot
from jonbot.layer3_data_layer.database.get_or_create_mongo_database_manager import get_or_create_mongo_database_manager
from jonbot.models import ChatRequest, ChatResponse
from jonbot.system.logging.get_or_create_logger import logger


async def chat(chat_request: ChatRequest) -> ChatResponse:
    logger.info(f"Received chat request: {chat_request}")

    mongo_database = await get_or_create_mongo_database_manager()
    conversation_history = await mongo_database.get_conversation_history(
        context_route=chat_request.conversation_context.context_route)

    ai_chat_bot = await AIChatBot.build(conversation_context=chat_request.conversation_context,
                                        conversation_history=conversation_history, )
    ai_chat_bot.add_callback_handler(StreamingStdOutCallbackHandler())
    chat_response = await ai_chat_bot.get_chat_response(chat_input_string=chat_request.chat_input.message)

    return chat_response

import asyncio
import logging
from typing import AsyncIterable, Awaitable

from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.runnable import RunnableMap
from starlette.responses import StreamingResponse

from jonbot.layer2_core_processes.ai_chatbot.ai_chatbot import AIChatBot
from jonbot.layer2_core_processes.ai_chatbot.components.callbacks.callbacks import StreamingAsyncCallbackHandler
from jonbot.layer3_data_layer.database.get_or_create_mongo_database_manager import get_or_create_mongo_database_manager
from jonbot.models.conversation_models import ChatRequest

logger = logging.getLogger(__name__)


async def chat_stream_bot(chat_request: ChatRequest):
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


async def stream_chat_expression_lang(chat_request: ChatRequest) -> AsyncIterable[str]:
    callback, chain = await create_chain_with_expression_language()

    async def wrap_done(awaitable_function: Awaitable, event: asyncio.Event):
        """Wrap an awaitable with a event to signal when it's done or an exception is raised."""
        try:
            await awaitable_function
        except Exception as e:
            logger.exception(e)
            raise

        finally:
            # Signal the aiter to stop.
            event.set()

    # Begin a task that runs in the background.

    task = asyncio.create_task(wrap_done(
        chain.ainvoke({"human_input": chat_request.chat_input.message}),
        callback.done),
    )

    async for token in callback.aiter():
        # Use server-sent-events to stream the response
        token_sse_format = f"data: {token}\n\n"
        logger.trace(f"Sending token: {token_sse_format}")
        yield token_sse_format

    await task



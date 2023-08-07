import logging
import time
import uuid

import aiohttp
import discord

from jonbot.layer0_frontends.discord_bot.utilities.get_context_from_message import \
    get_conversational_context_from_discord_message
from jonbot.layer0_frontends.discord_bot.utilities.get_conversation_history_from_message import \
    get_conversation_history_from_message
from jonbot.layer1_api_interface.app import API_CHAT_URL, API_CHAT_STREAM_URL
from jonbot.layer3_data_layer.data_models.conversation_models import ChatInput, ChatResponse, ChatRequest, \
    ChatRequestConfig
from jonbot.layer3_data_layer.database.mongo_database import MongoDatabaseManager, CONVERSATION_HISTORY_COLLECTION_NAME

logger = logging.getLogger(__name__)

conversations = {}


async def handle_text_message(message: discord.Message,
                              mongo_database_manager: MongoDatabaseManager,
                              streaming: bool = False,
                              ):
    async with aiohttp.ClientSession() as session:
        chat_input = ChatInput(message=message.content,
                               uuid=str(uuid.uuid4()),
                               )

        conversational_context = get_conversational_context_from_discord_message(message=message)

        await update_conversation_history_in_database(mongo_database_manager=mongo_database_manager,
                                                      message=message)

        chat_request = ChatRequest(chat_input=chat_input,
                                   conversational_context=conversational_context,
                                   config=ChatRequestConfig()
                                   )

        if streaming:
            api_route = API_CHAT_STREAM_URL
        else:
            api_route = API_CHAT_URL

        logger.info(f"Sending chat request payload: {chat_request.dict()}")
        async with session.post(api_route, json=chat_request.dict()) as response:
            if response.status == 200:
                data = await response.json()
                chat_response = ChatResponse(**data)
                await message.reply(chat_response.message)
                logger.info(f"ChatRequest payload sent: \n {chat_request.dict()}\n "
                            f"ChatResponse payload received: \n {chat_response.dict()}")
            else:
                error_message = f"Received non-200 response code: {response.status} - {await response.text()}"
                logger.exception(error_message)

                await message.reply(
                    f"Sorry, I'm currently unable to process your request. \n  > {error_message}")


async def update_conversation_history_in_database(mongo_database_manager: MongoDatabaseManager,
                                                  message: discord.Message):
    tic = time.perf_counter()
    conversation_history = await get_conversation_history_from_message(message=message)

    toc = time.perf_counter()
    logger.debug(
        f"get_conversation_history_from_message() took {toc - tic:0.4f} seconds and returned: {len(conversation_history)} messages)")

    tic = time.perf_counter()
    await mongo_database_manager.upsert(collection_name=CONVERSATION_HISTORY_COLLECTION_NAME,
                                        data={**conversation_history.dict()})
    toc = time.perf_counter()

    logger.debug(
        f"mongo_database_manager.upsert() took {toc - tic:0.4f} seconds to upsert {len(conversation_history)} messages)")

    logger.info(f"Updated conversation history for context_route_key: {conversation_history.context_route}")

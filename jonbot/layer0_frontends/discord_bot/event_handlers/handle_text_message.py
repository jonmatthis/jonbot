import logging
import time

import aiohttp
import discord

from jonbot.layer0_frontends.discord_bot.utilities.get_conversation_history_from_message import \
    get_conversation_history_from_message
from jonbot.layer1_api_interface.app import API_CHAT_URL, API_CHAT_STREAM_URL
from jonbot.layer3_data_layer.data_models.conversation_models import ChatResponse, ChatRequest, \
    ContextRoute
from jonbot.layer3_data_layer.database.mongo_database import MongoDatabaseManager, CONVERSATION_HISTORY_COLLECTION_NAME

logger = logging.getLogger(__name__)

conversations = {}


async def send_request_to_api(api_route: str, chat_request: ChatRequest):
    async with aiohttp.ClientSession() as session:
        response = await session.post(api_route, json=chat_request.dict())

        if response.status == 200:
            return await response.json()
        else:
            error_message = await error_message_from_response(response)
            logger.exception(error_message)
            raise aiohttp.ClientResponseError(response.status, error_message)


async def error_message_from_response(response):
    error_message = f"Received non-200 response code: {response.status} - {await response.text()}"
    return error_message


async def handle_text_message(message: discord.Message,
                              mongo_database_manager: MongoDatabaseManager,
                              streaming: bool = False,
                              ):
    async with aiohttp.ClientSession() as session:

        await update_conversation_history_in_database(mongo_database_manager=mongo_database_manager,
                                                      message=message)

        chat_request = ChatRequest.from_discord_message(message=message, )

        if streaming:
            api_route = API_CHAT_STREAM_URL
        else:
            api_route = API_CHAT_URL

        logger.info(f"Sending chat request payload: {chat_request.dict()}")

        response = await send_request_to_api(api_route=api_route, chat_request=chat_request)

        if response.status == 200:
            data = await response.json()
            chat_response = ChatResponse(**data)
            await message.reply(chat_response.message)
            logger.info(f"ChatRequest payload sent: \n {chat_request.dict()}\n "
                        f"ChatResponse payload received: \n {chat_response.dict()}")
        else:
            await message.reply(
                f"Sorry, I'm currently unable to process your request. \n  > {error_message_from_response(response)}")


async def update_conversation_history_in_database(mongo_database_manager: MongoDatabaseManager,
                                                  message: discord.Message):

    await mongo_database_manager.upsert(collection_name=CONVERSATION_HISTORY_COLLECTION_NAME,
                                        data={"context_route": ContextRoute.from_discord_message(message=message,
                                                                                                 parent_route_only = True),
                                              "conversation_history": await get_conversation_history_from_message(
                                                  message=message)}
                                        )

    logger.info(
        f"Updated conversation history for context_route_key: {ContextRoute.from_discord_message(message=message)}")

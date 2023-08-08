import logging

import aiohttp
import discord

from jonbot.layer0_frontends.discord_bot.utilities.get_conversation_history_from_message import \
    get_conversation_history_from_message
from jonbot.layer1_api_interface.app import API_CHAT_URL, API_CHAT_STREAM_URL, API_DATABASE_UPSERT_URL
from jonbot.layer1_api_interface.send_request_to_api import send_request_to_api, error_message_from_response
from jonbot.layer3_data_layer.data_models.conversation_models import ChatResponse, ChatRequest, \
    ContextRoute
from jonbot.layer3_data_layer.data_models.database_upsert_models import DatabaseUpsertRequest
from jonbot.layer3_data_layer.database.mongo_database import CONVERSATION_HISTORY_COLLECTION_NAME

logger = logging.getLogger(__name__)

conversations = {}


async def handle_text_message(message: discord.Message,
                              streaming: bool = False,
                              ):
    async with aiohttp.ClientSession() as session:

        await update_conversation_history_in_database(message=message)

        chat_request = ChatRequest.from_discord_message(message=message, )

        if streaming:
            api_route = API_CHAT_STREAM_URL
        else:
            api_route = API_CHAT_URL

        logger.info(f"Sending chat request payload: {chat_request.dict()}")

        response = await send_request_to_api(api_route=api_route, data=chat_request.dict())

        if response:
            chat_response = ChatResponse(**response)
            await message.reply(chat_response.message)
            logger.info(f"ChatRequest payload sent: \n {chat_request.dict()}\n "
                        f"ChatResponse payload received: \n {chat_response.dict()}"
                        f"Successfully sent chat request payload to API!")

        else:
            await message.reply(
                f"Sorry, I'm currently unable to process your request. \n  > {error_message_from_response(response)}")


async def update_conversation_history_in_database(message: discord.Message):
    conversation_history = await get_conversation_history_from_message(message=message)
    upsert_request = DatabaseUpsertRequest(collection=CONVERSATION_HISTORY_COLLECTION_NAME,
                                           data=conversation_history.dict(),
                                           query={"context_route_parent": ContextRoute.from_discord_message(message=message).parent},
                                           )
    await send_request_to_api(api_route=API_DATABASE_UPSERT_URL,
                              data=upsert_request.dict())

    logger.info(
        f"Updated conversation history for context_route_key: {ContextRoute.from_discord_message(message=message)}")

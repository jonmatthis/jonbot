import logging

import aiohttp
import discord

from jonbot.layer0_frontends.discord_bot.api_requests.send_chat_api_request import send_chat_api_request
from jonbot.layer0_frontends.discord_bot.api_requests.send_chat_stream_api_request import send_chat_stream_api_request
from jonbot.layer0_frontends.discord_bot.utilities.get_conversation_history_from_message import \
    get_conversation_history_from_message
from jonbot.layer1_api_interface.app import get_api_endpoint_url, CHAT_STREAM_ENDPOINT, \
    CHAT_ENDPOINT, DATABASE_UPSERT_ENDPOINT, send_request_to_api
from jonbot.layer3_data_layer.data_models.conversation_models import ChatRequest, \
    ContextRoute
from jonbot.layer3_data_layer.data_models.database_upsert_models import DatabaseUpsertRequest
from jonbot.layer3_data_layer.database.mongo_database import CONVERSATION_HISTORY_COLLECTION_NAME

logger = logging.getLogger(__name__)

conversations = {}


async def handle_text_message(message: discord.Message,
                              streaming: bool,
                              ):
    async with aiohttp.ClientSession() as session:

        await update_conversation_history_in_database(message=message)

        chat_request = ChatRequest.from_discord_message(message=message, )

        if streaming:
            await send_chat_stream_api_request(api_route=get_api_endpoint_url(CHAT_STREAM_ENDPOINT),
                                               chat_request=chat_request,
                                               message=message)
        else:
            await send_chat_api_request(api_route=get_api_endpoint_url(CHAT_ENDPOINT),
                                        chat_request=chat_request,
                                        message=message)


async def update_conversation_history_in_database(message: discord.Message):
    conversation_history = await get_conversation_history_from_message(message=message)
    upsert_request = DatabaseUpsertRequest(collection=CONVERSATION_HISTORY_COLLECTION_NAME,
                                           data=conversation_history.dict(),
                                           query={"context_route_parent": ContextRoute.from_discord_message(
                                               message=message).parent},
                                           )
    await send_request_to_api(api_endpoint=DATABASE_UPSERT_ENDPOINT,
                              data=upsert_request.dict())

    logger.info(
        f"Updated conversation history for context_route_key: {ContextRoute.from_discord_message(message=message)}")

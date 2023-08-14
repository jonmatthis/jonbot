import logging

import aiohttp
import discord

from jonbot.layer0_frontends.discord_bot.api_requests.send_chat_api_request import send_chat_api_request
from jonbot.layer0_frontends.discord_bot.api_requests.send_chat_stream_api_request import discord_send_chat_stream_api_request
from jonbot.layer0_frontends.discord_bot.utilities.get_conversation_history_from_message import \
    get_conversation_history_from_message
from jonbot.layer1_api_interface.api_client.get_or_create_api_client import api_client
from jonbot.layer1_api_interface.routes import DATABASE_UPSERT_ENDPOINT
from jonbot.models.conversation_models import ChatRequest, ContextRoute
from jonbot.models.database_upsert_models import DatabaseUpsertRequest
from jonbot.system.environment_config.environment_variables import CONVERSATION_HISTORY_COLLECTION_NAME

logger = logging.getLogger(__name__)

conversations = {}


async def handle_text_message(message: discord.Message,
                              streaming: bool,
                              ):

    await update_conversation_history_in_database(message=message)

    chat_request = ChatRequest.from_discord_message(message=message, )

    if streaming:
        await discord_send_chat_stream_api_request(chat_request=chat_request,
                                                   message=message)
    else:
        await send_chat_api_request(chat_request=chat_request,
                                    message=message)


async def update_conversation_history_in_database(message: discord.Message):
    conversation_history = await get_conversation_history_from_message(message=message)
    upsert_request = DatabaseUpsertRequest(collection=CONVERSATION_HISTORY_COLLECTION_NAME,
                                           data=conversation_history.dict(),
                                           query={"context_route_parent": ContextRoute.from_discord_message(
                                               message=message).parent},
                                           )

    await api_client.send_request_to_api(endpoint_name=DATABASE_UPSERT_ENDPOINT,
                                         data=upsert_request.dict())

    logger.info(
        f"Updated conversation history for context_route_key: {ContextRoute.from_discord_message(message=message)}")

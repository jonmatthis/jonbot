import aiohttp
import discord

from jonbot.layer0_frontends.discord_bot.api_requests.send_chat_api_request import send_chat_api_request
from jonbot.layer0_frontends.discord_bot.api_requests.send_chat_stream_api_request import send_chat_stream_api_request
from jonbot.layer0_frontends.discord_bot.utilities.get_conversation_history_from_message import \
    get_conversation_history_from_message
from jonbot.layer1_api_interface.api_client.get_or_create_api_client import api_client
from jonbot.layer1_api_interface.routes import CHAT_STREAM_ENDPOINT, CHAT_ENDPOINT, DATABASE_UPSERT_ENDPOINT
from jonbot.models.api_endpoint_url import ApiRoute
from jonbot.models.conversation_models import ChatRequest, ContextRoute
from jonbot.models.database_upsert_models import DatabaseUpsertRequest
from jonbot.system.environment_variables import CONVERSATION_HISTORY_COLLECTION_NAME
from jonbot.system.logging.get_or_create_logger import logger

conversations = {}


async def handle_text_message(message: discord.Message,
                              streaming: bool,
                              ):
    async with aiohttp.ClientSession() as session:

        await update_conversation_history_in_database(message=message)

        chat_request = ChatRequest.from_discord_message(message=message, )

        if streaming:
            await send_chat_stream_api_request(api_route=ApiRoute.from_endpoint(CHAT_STREAM_ENDPOINT),
                                               chat_request=chat_request,
                                               message=message)
        else:
            await send_chat_api_request(api_route=ApiRoute.from_endpoint(CHAT_ENDPOINT),
                                        chat_request=chat_request,
                                        message=message)


async def update_conversation_history_in_database(message: discord.Message):
    conversation_history = await get_conversation_history_from_message(message=message)
    upsert_request = DatabaseUpsertRequest(collection=CONVERSATION_HISTORY_COLLECTION_NAME,
                                           data=conversation_history.dict(),
                                           query={"context_route_parent": ContextRoute.from_discord_message(
                                               message=message).parent},
                                           )

    await api_client.send_request_to_api(api_endpoint=DATABASE_UPSERT_ENDPOINT,
                                         data=upsert_request.dict())

    logger.info(
        f"Updated conversation history for context_route_key: {ContextRoute.from_discord_message(message=message)}")

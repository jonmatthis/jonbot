import logging
import uuid

import aiohttp
import discord

from jonbot.layer0_frontends.discord_bot.utilities.get_context.get_context_from_message import \
    get_conversational_context_from_message
from jonbot.layer0_frontends.discord_bot.utilities.get_context.get_conversation_history_from_message import \
    get_conversation_history_from_message
from jonbot.layer1_api_interface.app import API_CHAT_URL, API_CHAT_STREAM_URL
from jonbot.layer3_data_layer.data_models.conversation_models import ChatInput, ChatResponse, ChatRequest, \
    ChatRequestConfig, BotInfo
from jonbot.layer3_data_layer.data_models.discord_message import DiscordMessageDocument
from jonbot.layer3_data_layer.database.mongo_database import mongo_database_manager

logger = logging.getLogger(__name__)

#TODO - this `conversations` dict is a temporary solution to keep track of conversations. It should be replaced with something involving the database.
conversations = {}


def get_chat_request_config(discord_bot: discord.Bot):
    return ChatRequestConfig(
        bot_info=BotInfo(
            name=discord_bot.user.name,
            id=discord_bot.user.id,
        )
    )


async def handle_text_message(message: discord.Message,
                              discord_bot: discord.Bot,
                              streaming: bool = False,
                              ):
    global conversations
    async with aiohttp.ClientSession() as session:
        chat_input = ChatInput(message=message.content,
                               uuid=str(uuid.uuid4()),
                               )

        conversational_context = get_conversational_context_from_message(message=message)

        if conversational_context.context_route in conversations.keys():
            conversation_history = conversations[conversational_context.context_route]
        else:
            conversation_history = await get_conversation_history_from_message(message=message)
            conversations[conversational_context.context_route] = conversation_history

        chat_request = ChatRequest(chat_input=chat_input,
                                   # conversational_context=conversational_context,
                                   # conversation_history=conversation_history,
                                   # config=get_chat_request_config(discord_bot=discord_bot)
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
                discord_message_document = DiscordMessageDocument.from_message(message=message).dict()
                mongo_database_manager.upsert(collection_name="discord_messages",
                                              data=discord_message_document, )
            else:
                error_message = f"Received non-200 response code: {response.status} - {await response.text()}"
                logger.exception(error_message)

                await message.reply(
                    f"Sorry, I'm currently unable to process your request. \n > {error_message}")

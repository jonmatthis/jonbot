import asyncio
import logging

import discord

from jonbot.layer0_frontends.discord_bot.api_requests.send_streaming_test_request import streaming_response_test_endpoint
from jonbot.layer1_api_interface.send_request_to_api import send_request_to_api_streaming
from jonbot.layer3_data_layer.data_models.conversation_models import ChatRequest

logger = logging.getLogger(__name__)
class DiscordStreamUpdater:
    def __init__(self):
        self.message_content = ""
        self.reply_message = None
        self.max_message_length = 2000

    async def initialize_reply(self, message: discord.Message):
        logger.info(f"initializing reply to message: `{message.id}`")
        self.reply_message = await message.reply("`awaiting bot response...`")

    async def update_discord_reply(self, token: str):
        logger.debug(f"updating discord reply with token: `{token}`")
        comfy_message_length = int(self.max_message_length * .9)
        self.message_content += token

        if len(self.message_content) > comfy_message_length:
            await self.reply_message.edit(content=self.message_content)
            self.reply_message = await self.reply_message.reply("`continuing from previous message...`\n\n")
            self.message_content = token

        await self.reply_message.edit(content=self.message_content)

async def send_chat_stream_api_request(api_route: str,
                                       chat_request: ChatRequest,
                                       message: discord.Message):
    updater = DiscordStreamUpdater()
    await updater.initialize_reply(message)

    async def callback(token: str):
        logger.debug(f"frontend received token: `{token}`")
        await updater.update_discord_reply(token)

    try:
        return await send_request_to_api_streaming(api_route=api_route,
                                                   data=chat_request.dict(),
                                                   callbacks=[callback])
    except Exception as e:
        await updater.update_discord_reply(f"Error while streaming reply: \n >  {e}")
        raise e

import asyncio
import logging

import discord

from jonbot.layer0_frontends.discord_bot.api_requests.send_streaming_test_request import streaming_response_test_endpoint
from jonbot.layer1_api_interface.send_request_to_api import send_request_to_api_streaming
from jonbot.layer3_data_layer.data_models.conversation_models import ChatRequest

logger = logging.getLogger(__name__)
class DiscordStreamUpdater:
    def __init__(self):
        self.message_content = ""
        self.reply_message = None
        self.max_message_length = 2000

    async def initialize_reply(self, message: discord.Message):
        logger.info(f"initializing reply to message: `{message.id}`")
        self.reply_message = await message.reply("`awaiting bot response...`")

    async def update_discord_reply(self, token: str):
        logger.debug(f"updating discord reply with token: `{token}`")
        comfy_message_length = int(self.max_message_length * .9)
        self.message_content += token

        if len(self.message_content) > comfy_message_length:
            await self.reply_message.edit(content=self.message_content)
            self.reply_message = await self.reply_message.reply("`continuing from previous message...`\n\n")
            self.message_content = token

        await self.reply_message.edit(content=self.message_content)

async def send_chat_stream_api_request(api_route: str,
                                       chat_request: ChatRequest,
                                       message: discord.Message):
    updater = DiscordStreamUpdater()
    await updater.initialize_reply(message)

    async def callback(token: str):
        logger.debug(f"Frontend received token: `{token}`")
        await updater.update_discord_reply(token)

    try:
        return await send_request_to_api_streaming(api_route=api_route,
                                                   data=chat_request.dict(),
                                                   callbacks=[callback])
    except Exception as e:
        await updater.update_discord_reply(f"Error while streaming reply: \n >  {e}")
        raise e




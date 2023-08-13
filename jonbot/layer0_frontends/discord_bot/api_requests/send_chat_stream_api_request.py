import logging

import discord

from jonbot.layer1_api_interface.api_client.get_or_create_api_client import api_client
from jonbot.layer1_api_interface.routes import CHAT_STREAM_ENDPOINT
from jonbot.models.conversation_models import ChatRequest

logger = logging.getLogger(__name__)


class DiscordStreamUpdater:
    def __init__(self):
        self.message_content = ""
        self.reply_message = None
        self.max_message_length = 2000
        self.comfy_message_length = int(self.max_message_length * .9)

    async def initialize_reply(self, message: discord.Message):
        logger.info(f"initializing reply to message: `{message.id}`")
        self.reply_message = await message.reply("response incoming...")

    async def update_discord_reply(self, token: str):
        clean_token = token.replace("data: ", "").replace("data:", "").replace("\n\n", "")
        if not clean_token == "":
            logger.trace(f"updating discord reply with token: received: `{token}`,  cleaned: `{clean_token}`")
            self.message_content += clean_token
            await self.reply_message.edit(content=self.message_content)


            if len(self.message_content) > self.comfy_message_length:
                logger.trace(
                    f"message content (len: {len(self.message_content)}) is longer than comfy message length: {self.comfy_message_length} - continuing in next message...")
                self.message_content = "`continuing from previous message...`\n"
                self.reply_message = await self.reply_message.reply(self.message_content)




async def discord_send_chat_stream_api_request(chat_request: ChatRequest,
                                               message: discord.Message):
    updater = DiscordStreamUpdater()
    await updater.initialize_reply(message)

    async def callback(token: str):
        logger.trace(f"Frontend received token: `{token}`")
        clean_token = token.replace("data: ", "").replace("\n\n", "")
        await updater.update_discord_reply(clean_token)

    try:
        return await api_client.send_request_to_api_streaming(endpoint_name=CHAT_STREAM_ENDPOINT,
                                                              data=chat_request.dict(),
                                                              callbacks=[callback])
    except Exception as e:
        await updater.update_discord_reply(f"Error while streaming reply: \n >  {e}")
        raise

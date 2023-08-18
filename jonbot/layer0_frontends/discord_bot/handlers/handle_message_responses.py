import discord

from jonbot import get_logger
from jonbot.layer0_frontends.discord_bot.handlers.should_process_message import RESPONSE_INCOMING_TEXT
from jonbot.models.conversation_models import ChatResponse

logger = get_logger()

STOP_STREAMING_TOKEN = "STOP_STREAMING"


class DiscordStreamUpdater:
    def __init__(self):
        self.message_content = ""
        self.reply_message = None
        self.max_message_length = 2000
        self.comfy_message_length = int(self.max_message_length * .9)
        self.done = False

    async def initialize_reply(self, message: discord.Message):
        logger.info(f"initializing reply to message: `{message.id}`")
        self.reply_message = await message.reply(RESPONSE_INCOMING_TEXT)

    async def update_discord_reply(self, token: str):
        stop_now = False
        if STOP_STREAMING_TOKEN in token:
            logger.info(f"stopping stream")
            stop_now = True
            token = token.replace(STOP_STREAMING_TOKEN, "")

        if not token == "":
            logger.trace(f"updating discord reply with token: {repr(token)}")
            self.message_content += token
            await self.reply_message.edit(content=self.message_content)

            if len(self.message_content) > self.comfy_message_length:
                logger.trace(
                    f"message content (len: {len(self.message_content)}) is longer than comfy message length: {self.comfy_message_length} - continuing in next message...")
                self.message_content = "`continuing from previous message...`\n"
                self.reply_message = await self.reply_message.reply(self.message_content)
        if stop_now:
            self.done = True
            logger.info(f"done streaming")


async def update_discord_message(chat_response: ChatResponse,
                                 message: discord.Message,
                                 max_message_length: int = 2000):
    comfy_message_length = int(max_message_length * .9)
    if len(chat_response.text) > comfy_message_length:
        await handle_long_message(chat_response, max_message_length, message)
    else:
        await message.edit(content=chat_response.text)


async def handle_long_message(chat_response, max_message_length, message):
    message_chunks = [chat_response.text[index:index + max_message_length] for index in
                      range(0, len(chat_response.text), max_message_length)]
    for chunk_number, message_chunk in enumerate(message_chunks):
        message = await message.edit(
            content=f"`Message {chunk_number + 1} out of {len(message_chunks)}` {message_chunk}")

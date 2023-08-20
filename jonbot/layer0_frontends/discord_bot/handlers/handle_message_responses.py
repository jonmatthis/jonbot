import asyncio

import discord

from jonbot import get_logger
from jonbot.layer0_frontends.discord_bot.handlers.should_process_message import RESPONSE_INCOMING_TEXT
from jonbot.models.conversation_models import ChatResponse

logger = get_logger()

STOP_STREAMING_TOKEN = "STOP_STREAMING"


class DiscordMessageResponder:
    def __init__(self):
        self.message_content = ""
        self._reply_message = None
        self._reply_messages = []
        self.max_message_length = 2000
        self.comfy_message_length = int(self.max_message_length * .9)
        self.done = False

    @property
    def reply_messages(self):
        self._add_reply_message_to_list(self._reply_message)
        return self._reply_messages

    async def initialize_reply(self,
                               message: discord.Message,
                               initial_message_content: str = RESPONSE_INCOMING_TEXT):
        logger.info(f"initializing reply to message: `{message.id}`")
        self._reply_message = await message.reply(initial_message_content)

    async def update_reply(self, token: str, pause_duration: float = 0.1):
        stop_now = False
        if STOP_STREAMING_TOKEN in token:
            logger.info(f"stopping stream")
            stop_now = True
            token = token.replace(STOP_STREAMING_TOKEN, "")

        if not token == "":
            logger.trace(f"updating discord reply with token: {repr(token)}")
            self.message_content += token
            await asyncio.sleep(pause_duration)  # sleep to give discord time to update the message

            if len(self.message_content) > self.comfy_message_length:
                logger.trace(
                    f"message content (len: {len(self.message_content)}) is longer than comfy message length: {self.comfy_message_length} - continuing in next message...")
                self._add_reply_message_to_list(self._reply_message)

                self.message_content = "`continuing from previous message...`\n"
                self._reply_message = await self._reply_message.reply(self.message_content)
            else:
                await self._reply_message.edit(content=self.message_content)

        if stop_now:
            self.done = True
            logger.info(f"done streaming")


    def _add_reply_message_to_list(self, _reply_message:discord.Message):
        self._reply_message.content = self.message_content #I'm not sure why this needs done, but without it the conent still reads "response incoming" when the message is logged in the db
        self._reply_messages.append(_reply_message)

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

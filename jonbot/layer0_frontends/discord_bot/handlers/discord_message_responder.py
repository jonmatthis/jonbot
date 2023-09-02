import asyncio
import time

import discord

from jonbot import get_jonbot_logger
from jonbot.layer0_frontends.discord_bot.handlers.should_process_message import (
    RESPONSE_INCOMING_TEXT,
)

logger = get_jonbot_logger()

STOP_STREAMING_TOKEN = "STOP_STREAMING"


class DiscordMessageResponder:
    def __init__(self):
        self.message_content = ""
        self._reply_message = None
        self._reply_messages = []
        self.max_message_length = 2000
        self.comfy_message_length = int(self.max_message_length * 0.9)
        self.done = False

        self._token_queue = asyncio.Queue()
        self.loop_task = None
        self._previous_timestamp = time.perf_counter()

    async def get_reply_messages(self):
        await self._add_reply_message_to_list()
        return self._reply_messages

    async def initialize(
            self,
            message: discord.Message,
            initial_message_content: str = RESPONSE_INCOMING_TEXT,
    ):
        logger.info(f"initializing reply to message: `{message.id}`")
        self._reply_message = await message.reply(initial_message_content)
        logger.debug(f"initialized reply to message: `{message.id}`")
        self.loop_task = asyncio.create_task(
            self._run_token_queue_loop()
        )  # Start the queue loop

    async def add_token_to_queue(self, token: str):
        logger.trace(
            f"FRONTEND - adding token to queue: {repr(token)}, token_queue size: {self._token_queue.qsize()}"
        )
        await self._token_queue.put(token)

    async def _run_token_queue_loop(self, delay: float = 0.1, chunk_size: int = 10):
        chunk = []
        while True:
            await asyncio.sleep(delay)
            if self._token_queue.empty():
                logger.trace(
                    f"FRONTEND - token_queue is empty, waiting {delay} seconds"
                )
                await asyncio.sleep(delay)
                if self.done:
                    logger.trace(
                        f"FRONTEND - self.done is True and token_queue is empty, breaking token_queue_loop!"
                    )
                    break
            else:
                while not self._token_queue.empty():
                    token = await self._token_queue.get()
                    chunk.append(token)
                    logger.trace(
                        f"FRONTEND - de-queueing  token: {repr(token)} (token_queue size: {self._token_queue.qsize()})"
                    )
                    if len(chunk) > chunk_size:
                        await self.add_text_to_reply_message("".join(chunk))
                        chunk = []

        logger.trace(f"Appending final chunk to reply message {chunk}...")
        await self.add_text_to_reply_message("".join(chunk))
        logger.info(f"queue loop finished")

    async def add_text_to_reply_message(self, chunk: str, show_delta_t: bool = False):
        stop_now = False
        if STOP_STREAMING_TOKEN in chunk:
            logger.debug(f"Recieved `{STOP_STREAMING_TOKEN}`, stopping stream...")
            stop_now = True
            chunk = chunk.replace(STOP_STREAMING_TOKEN, "")

        if not chunk == "":
            logger.trace(f"FRONTEND - updating discord reply with chunk: {repr(chunk)}")

            if show_delta_t:  # append delta_t to chunk, useful for debugging
                chunk = self._add_delta_t_to_token(chunk)

            self.message_content += chunk

            if len(self.message_content) > self.comfy_message_length:
                logger.trace(
                    f"message content (len: {len(self.message_content)}) is longer than comfy message length: {self.comfy_message_length} - continuing in next message..."
                )
                await self._add_reply_message_to_list()

                self.message_content = f"`continuing from previous message...`\n\n {chunk}"
                self._reply_message = await self._reply_message.reply(
                    self.message_content
                )
            else:
                await self._reply_message.edit(content=self.message_content)

        if stop_now:
            logger.debug(f"Stopping stream (setting `self.done` to True)...")
            self.done = True

    def _add_delta_t_to_token(self, chunk: str):
        current_timestamp = time.perf_counter()
        updated_token = (
            f"[delta_t:{current_timestamp - self._previous_timestamp:.6f}]{chunk}\n"
        )
        self._previous_timestamp = current_timestamp
        return updated_token

    async def _add_reply_message_to_list(
            self,
    ):
        self._reply_message.content = (
            self.message_content
        )  # I'm not sure why this needs done, but without it the conent still reads "response incoming" when the message is logged in the db
        self._reply_messages.append(self._reply_message)

    async def shutdown(self):
        self.done = True
        logger.debug(f"Message Responder shutting down...")
        if self.loop_task:
            await self.loop_task

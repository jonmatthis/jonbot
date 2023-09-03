import asyncio
import tempfile
import time
from pathlib import Path
from typing import List

import discord

from jonbot import get_jonbot_logger
from jonbot.layer0_frontends.discord_bot.handlers.should_process_message import (
    RESPONSE_INCOMING_TEXT,
)

logger = get_jonbot_logger()

STOP_STREAMING_TOKEN = "STOP_STREAMING"


class DiscordMessageResponder:
    def __init__(self, message_prefix: str = ""):
        self.message_prefix: str = message_prefix
        self.message_content: str = self.message_prefix
        self._reply_message: discord.Message = None
        self._reply_messages: List[discord.Message] = []
        self._full_message_content: str = ""
        self.max_message_length: int = 2000
        self.comfy_message_length: int = int(self.max_message_length * 0.9)
        self.done: bool = False

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
        self._full_message_content += token
        await self._token_queue.put(token)

    async def _run_token_queue_loop(self, base_delay: float = 0.1, chunk_size: int = 10):
        chunk = []
        delay = base_delay
        while True:
            await asyncio.sleep(delay)
            delay *= 1.1
            if self._token_queue.empty():
                logger.trace(
                    f"FRONTEND - token_queue is empty, waiting {delay:.2f} seconds"
                )
                await asyncio.sleep(base_delay)
                if self.done:
                    logger.trace(
                        f"FRONTEND - self.done is True and token_queue is empty, breaking token_queue_loop!"
                    )
                    break
            else:
                delay = base_delay
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
        if len(self._reply_messages) > 0:
            await self._send_full_text_as_attachment()
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
                await self.handle_message_length_overflow(chunk)

            else:
                await self._reply_message.edit(content=self.message_content)

        if stop_now:
            logger.debug(f"Stopping stream (setting `self.done` to True)...")
            self.done = True

    async def handle_message_length_overflow(self, chunk: str):
        chunks = []

        for start_index in range(0, len(chunk), self.comfy_message_length):
            chunks.append(chunk[start_index:start_index + self.comfy_message_length])
        for chunk in chunks:
            logger.trace(
                f"message content (len: {len(chunk)}) is longer than comfy message length: {self.comfy_message_length} - continuing in next message..."
            )
            new_message_initial_content: str = f"{self.message_prefix}continuing from: \n\n > {chunk} \n\n"
            new_message: discord.Message = await self._reply_message.reply(
                new_message_initial_content, mention_author=False
            )
            self.message_content += f"\n\n `continued in next message:`\n {new_message.jump_url}"
            await self._reply_message.edit(content=self.message_content)
            self.message_content = new_message_initial_content
            await self._add_reply_message_to_list()
            self._reply_message = new_message

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

    async def _send_full_text_as_attachment(self):
        logger.debug(f"Sending full text as attachment...")
        temp_filepath = None  # initialize temp_filepath
        try:
            # create a temporary file
            with tempfile.NamedTemporaryFile('w',
                                             delete=False,
                                             suffix='.md',
                                             encoding='utf-8',
                                             ) as tf:
                tf.write(self._full_message_content)
                temp_filepath = tf.name

            # create a discord.File instance
            file = discord.File(temp_filepath)

            # send the file
            await self._reply_message.edit(files=[file])

        except Exception as e:
            # Handle any error that might occur
            logger.exception(f"An error occurred while sending the full text as an attachment: {str(e)}")
            raise

        finally:
            # Make sure the file is deleted, even if an error occurs
            if temp_filepath and Path(temp_filepath).exists():
                Path(temp_filepath).unlink()

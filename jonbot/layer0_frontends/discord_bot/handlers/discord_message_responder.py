import asyncio

import discord

from jonbot import get_logger
from jonbot.layer0_frontends.discord_bot.handlers.should_process_message import RESPONSE_INCOMING_TEXT

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

        self._token_queue = asyncio.Queue()
        self.loop_task = None

    async def get_reply_messages(self):
        await self._add_reply_message_to_list()
        return self._reply_messages

    async def initialize(self,
                         message: discord.Message,
                         initial_message_content: str = RESPONSE_INCOMING_TEXT):
        logger.info(f"initializing reply to message: `{message.id}`")
        self._reply_message = await message.reply(initial_message_content)
        logger.info(f"initialized reply to message: `{message.id}`")
        self.loop_task = asyncio.create_task(self._run_token_queue_loop())  # Start the queue loop

    async def add_token_to_queue(self, token: str):
        logger.trace(f"FRONTEND - adding token to queue: {repr(token)}, token_queue size: {self._token_queue.qsize()}")
        await self._token_queue.put(token)

    async def _run_token_queue_loop(self, delay: float = 0.1):

        while True:
            if self._token_queue.empty():
                logger.trace(f"token_queue is empty, waiting {delay} seconds")
                await asyncio.sleep(delay)
                if self.done:
                    logger.trace(f"self.done is True and token_queue is empty, breaking token_queue_loop!")
                    break
            else:
                while not self._token_queue.empty():
                    token = await self._token_queue.get()
                    logger.trace(f"getting token: {repr(token)} (token_queue size: {self._token_queue.qsize()})")
                    await self._update_reply_message(token)

        logger.info(f"queue loop finished")

    async def _update_reply_message(self, token: str):

        stop_now = False
        if STOP_STREAMING_TOKEN in token:
            logger.info(f"Recieved `{STOP_STREAMING_TOKEN}`, stopping stream...")
            stop_now = True
            token = token.replace(STOP_STREAMING_TOKEN, "")

        if not token == "":
            logger.trace(f"updating discord reply with token: {repr(token)}")
            self.message_content += token

            if len(self.message_content) > self.comfy_message_length:
                logger.trace(
                    f"message content (len: {len(self.message_content)}) is longer than comfy message length: {self.comfy_message_length} - continuing in next message...")
                await self._add_reply_message_to_list()

                self.message_content = "`continuing from previous message...`\n"
                self._reply_message = await self._reply_message.reply(self.message_content)
            else:
                await self._reply_message.edit(content=self.message_content)

        if stop_now:
            logger.info(f"Stopping stream (setting `self.done` to True)...")
            self.done = True


    async def _add_reply_message_to_list(self, ):
        self._reply_message.content = self.message_content  # I'm not sure why this needs done, but without it the conent still reads "response incoming" when the message is logged in the db
        self._reply_messages.append(self._reply_message)

    async def shutdown(self):
        self.done = True
        logger.debug(f"Message Responder shutting down...")
        if self.loop_task:
            await self.loop_task

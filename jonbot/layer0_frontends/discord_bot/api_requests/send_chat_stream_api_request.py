import asyncio

import discord

from jonbot.layer1_api_interface.app import API_STREAMING_RESPONSE_TEST_URL
from jonbot.layer1_api_interface.send_request_to_api import send_request_to_api_streaming
from jonbot.layer3_data_layer.data_models.conversation_models import ChatRequest


class DiscordStreamUpdater:
    def __init__(self):
        self.message_content = ""
        self.reply_message = None
        self.max_message_length = 2000

    async def initialize_reply(self, message: discord.Message):
        self.reply_message = await message.reply("`awaiting bot response...`")

    async def update_discord_reply(self, token: str):
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
        await updater.update_discord_reply(token)

    return await send_request_to_api_streaming(api_route=api_route,
                                               data=None,
                                               callbacks=[callback])


async def print_over_here(token):
    await asyncio.sleep(1)
    print(token)


async def streaming_response_test_endpoint():
    return await send_request_to_api_streaming(api_route=API_STREAMING_RESPONSE_TEST_URL,
                                               data={"test": "test"},
                                               callbacks=[print_over_here])


if __name__ == '__main__':
    asyncio.run(streaming_response_test_endpoint())

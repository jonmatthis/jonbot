import asyncio

import discord

from jonbot.layer1_api_interface.app import API_STREAMING_RESPONSE_TEST_URL
from jonbot.layer1_api_interface.send_request_to_api import send_request_to_api_streaming
from jonbot.layer3_data_layer.data_models.conversation_models import ChatRequest


async def send_chat_stream_api_request(api_route: str,
                                       chat_request: ChatRequest,
                                       message: discord.Message):
    reply_message = await message.reply("`awaiting bot response...`")

    async def update_discord_reply(token: str,
                                   reply_message: discord.Message = reply_message,
                                   max_message_length: int = 2000):
        comfy_message_length = int(max_message_length * .9)
        if len(reply_message.content) > comfy_message_length:
            reply_message = await reply_message.reply("`continuing from previous message...`")
        reply_message.edit(content=message.content + token)

    return await send_request_to_api_streaming(api_route=api_route,
                                               data=chat_request.dict(),
                                               callbacks=[update_discord_reply])


async def print_over_here(token):
    await asyncio.sleep(1)
    print(token)


async def streaming_response_test_endpoint():
    return await send_request_to_api_streaming(api_route=API_STREAMING_RESPONSE_TEST_URL,
                                               data={"test": "test"},
                                               callbacks=[print_over_here])


if __name__ == '__main__':
    asyncio.run(streaming_response_test_endpoint())

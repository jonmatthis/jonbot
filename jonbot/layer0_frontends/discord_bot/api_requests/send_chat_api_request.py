import logging

import discord

from jonbot.layer1_api_interface.api_client.get_or_create_api_client import api_client
from jonbot.layer1_api_interface.routes import CHAT_ENDPOINT
from jonbot.models.conversation_models import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)


async def send_chat_api_request(chat_request: ChatRequest,
                                message: discord.Message):
    logger.info(f"Sending chat request payload: {chat_request.dict()}")
    reply_message = await message.reply("`awaiting bot response...`")
    response = await api_client.send_request_to_api(endpoint_name=CHAT_ENDPOINT,
                                                    data=chat_request.dict())
    chat_response = ChatResponse(**response)
    await send_chat_response(chat_response, reply_message)
    logger.info(f"ChatRequest payload sent: \n {chat_request.dict()}\n "
                f"ChatResponse payload received: \n {chat_response.dict()}\n"
                f"Successfully sent chat request payload to API!")


async def send_chat_response(chat_response: ChatResponse,
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

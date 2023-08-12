import discord

from jonbot.models.conversation_models import ChatRequest, ChatResponse
from jonbot.system.logging.get_or_create_logger import logger


async def send_chat_api_request(api_route: str,
                                chat_request: ChatRequest,
                                message: discord.Message):
    logger.info(f"Sending chat request payload: {chat_request.dict()}")
    reply_message = await message.reply("`awaiting bot response...`")
    response = await send_request_to_api(api_route=api_route, data=chat_request.dict())
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

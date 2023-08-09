import logging

import discord

from jonbot.layer1_api_interface.send_request_to_api import send_request_to_api
from jonbot.layer3_data_layer.data_models.conversation_models import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)
async def send_chat_api_request(api_route:str,
                                chat_request:ChatRequest,
                                message:discord.Message):
    logger.info(f"Sending chat request payload: {chat_request.dict()}")
    response = await send_request_to_api(api_route=api_route, data=chat_request.dict())
    chat_response = ChatResponse(**response)
    await message.reply(chat_response.message)
    logger.info(f"ChatRequest payload sent: \n {chat_request.dict()}\n "
                f"ChatResponse payload received: \n {chat_response.dict()}"
                f"Successfully sent chat request payload to API!")



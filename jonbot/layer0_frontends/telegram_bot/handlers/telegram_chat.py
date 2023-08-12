import logging
import uuid

import aiohttp
from telegram import Update
from telegram.ext import ContextTypes

from jonbot.layer1_api_interface.app import CHAT_ENDPOINT, get_api_endpoint_url
from jonbot.models import ChatInput, ChatResponse
from jonbot.layer3_data_layer.database.get_or_create_mongo_database_manager import get_or_create_mongo_database_manager

logger = logging.getLogger('httpcore')
logger.setLevel(logging.INFO)
logger = logging.getLogger('telegram')
logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)



async def telegram_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_input = ChatInput(message=update.message.text,
                           uuid=str(uuid.uuid4()))

    await update.message.chat.send_action(action="typing")

    async with aiohttp.ClientSession() as session:
        async with session.post(get_api_endpoint_url(CHAT_ENDPOINT), json=chat_input.dict()) as response:
            if response.status == 200:
                data = await response.json()
                chat_response = ChatResponse(**data)

                await context.bot.send_message(chat_id=update.effective_chat.id, text=chat_response.text)
                mongo_database_manager = await get_or_create_mongo_database_manager()
                await mongo_database_manager.upsert(update.message, chat_response)
            else:
                error_message = f"Received non-200 response code: {response.status}"
                logger.error(error_message)
                await context.bot.send_message(chat_id=update.effective_chat.id, text=error_message)

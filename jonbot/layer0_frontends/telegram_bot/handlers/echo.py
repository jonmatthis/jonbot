import logging
import uuid

import aiohttp
from telegram import Update
from telegram.ext import filters, ContextTypes

from jonbot.layer1_api_interface.app import API_CHAT_URL
from jonbot.layer3_data_layer.data_models.conversation_models import ChatInput, ChatResponse
from jonbot.layer3_data_layer.database.mongo_database import mongo_database_manager


logger = logging.getLogger(__name__)
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_input = ChatInput(message=update.message.text,
                           uuid=str(uuid.uuid4()))

    async with aiohttp.ClientSession() as session:
        async with session.post(API_CHAT_URL, json=chat_input.dict()) as response:
            if response.status == 200:
                data = await response.json()
                chat_response = ChatResponse(**data)
                await context.bot.send_message(chat_id=update.effective_chat.id, text=chat_response.message)
                mongo_database_manager.insert_telegram_message(update.message, chat_response)
            else:
                error_message = f"Received non-200 response code: {response.status}"
                logger.error(error_message)
                await context.bot.send_message(chat_id=update.effective_chat.id, text=error_message)

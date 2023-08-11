import logging

import aiohttp
from telegram import Update
from telegram.ext import ContextTypes

from golembot.layer1_api_interface.app import API_VOICE_TO_TEXT_URL
from golembot.layer3_data_layer.data_models.conversation_models import ChatResponse
from golembot.layer3_data_layer.database.mongo_database import mongo_database_manager

logger = logging.getLogger(__name__)


async def audio_to_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with aiohttp.ClientSession() as session:
        async with session.get(update.message.audio.file_id) as response:
            audio_data = await response.read()

        async with session.post(API_VOICE_TO_TEXT_URL, data=audio_data) as response:
            if response.status == 200:
                data = await response.json()
                chat_response = ChatResponse(**data)
                await context.bot.send_message(chat_id=update.effective_chat.id, text=chat_response.text)
                mongo_database_manager.insert_telegram_message(update.message, chat_response)
            else:
                error_message = f"Received non-200 response code: {response.status}"
                logger.error(error_message)
                await context.bot.send_message(chat_id=update.effective_chat.id, text=error_message)

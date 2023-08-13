import logging
import uuid

import aiohttp
from telegram import Update
from telegram.ext import ContextTypes

from jonbot.layer1_api_interface.api_client.get_or_create_api_client import api_client
from jonbot.layer1_api_interface.routes import CHAT_ENDPOINT
from jonbot.layer3_data_layer.database.get_or_create_mongo_database_manager import get_or_create_mongo_database_manager
from jonbot.models.conversation_models import ChatInput, ChatResponse

logger = logging.getLogger('httpcore')
logger.setLevel(logging.INFO)
logger = logging.getLogger('telegram')
logger.setLevel(logging.INFO)

from jonbot.system.logging.configure_logging import logger


async def telegram_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_input = ChatInput(message=update.message.text,
                           uuid=str(uuid.uuid4()))

    await update.message.chat.send_action(action="typing")

    async with aiohttp.ClientSession() as session:
        async with session.post(api_client.get_api_endpoint_url(CHAT_ENDPOINT), json=chat_input.dict()) as response:
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

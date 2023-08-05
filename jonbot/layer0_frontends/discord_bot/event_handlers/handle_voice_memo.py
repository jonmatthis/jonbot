import logging

import aiohttp
import discord

from jonbot.layer1_api_interface.app import API_VOICE_TO_TEXT_URL
from jonbot.layer3_data_layer.data_models.conversation_models import ChatResponse
from jonbot.layer3_data_layer.data_models.voice_to_text_request import VoiceToTextRequest
from jonbot.layer3_data_layer.database.mongo_database import mongo_database_manager

logger = logging.getLogger(__name__)

TRANSCRIBED_AUDIO_PREFIX = "Transcribed audio message"

async def handle_voice_memo(message:discord.Message):
    async with aiohttp.ClientSession() as session:
        voice_to_text_request = VoiceToTextRequest(audio_file_url=message.attachments[0].url)
        async with session.post(API_VOICE_TO_TEXT_URL, json=voice_to_text_request.dict()) as response:
            if response.status == 200:
                voice_to_text_response = await response.json()

                await message.reply(f"{TRANSCRIBED_AUDIO_PREFIX} from user `{message.author}`:\n > {voice_to_text_response['text']}")
            else:
                error_message = f"Received non-200 response code: {response.status}"
                logger.exception(error_message)
                await message.reply(
                    f"Sorry, I'm currently unable to process your (audio transcriptiopn) request. {error_message}")

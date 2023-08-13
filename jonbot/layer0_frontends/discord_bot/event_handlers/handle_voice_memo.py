import logging

import discord

from jonbot.layer0_frontends.discord_bot.event_handlers.handle_text_message import \
    update_conversation_history_in_database
from jonbot.layer1_api_interface.api_client.get_or_create_api_client import api_client
from jonbot.layer1_api_interface.routes import VOICE_TO_TEXT_ENDPOINT
from jonbot.models.voice_to_text_request import VoiceToTextRequest

logger = logging.getLogger(__name__)

TRANSCRIBED_AUDIO_PREFIX = "Transcribed audio message"


async def handle_voice_memo(message: discord.Message):
    await update_conversation_history_in_database(message=message)

    voice_to_text_request = VoiceToTextRequest(audio_file_url=message.attachments[0].url)

    await send_voice_to_text_api_request(api_route=api_client.get_api_endpoint_url(VOICE_TO_TEXT_ENDPOINT),
                                         voice_to_text_request=voice_to_text_request,
                                         message=message
                                         )


async def send_voice_to_text_api_request(api_route: str,
                                         voice_to_text_request: VoiceToTextRequest,
                                         message: discord.Message):
    logger.info(f"Sending voice to text request payload: {voice_to_text_request.dict()}")
    reply_message = await message.reply("`awaiting bot response...`")
    response = await api_client.send_request_to_api(endpoint_name=VOICE_TO_TEXT_ENDPOINT,
                                                    data=voice_to_text_request.dict())
    await reply_message.reply(
        f"{TRANSCRIBED_AUDIO_PREFIX} from user `{message.author}`:\n > {response['text']}")
    logger.info(f"VoiceToTextResponse payload received: \n {response}\n"
                f"Successfully sent voice to text request payload to API!")

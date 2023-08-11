import logging

import discord

from jonbot.layer0_frontends.discord_bot.event_handlers.handle_text_message import \
    update_conversation_history_in_database
from jonbot.layer1_api_interface.app import get_api_endpoint_url, VOICE_TO_TEXT_ENDPOINT, send_request_to_api
from jonbot.layer3_data_layer.data_models.voice_to_text_request import VoiceToTextRequest

logger = logging.getLogger(__name__)

TRANSCRIBED_AUDIO_PREFIX = "Transcribed audio message"


async def handle_voice_memo(message: discord.Message):
    await update_conversation_history_in_database(message=message)

    voice_to_text_request = VoiceToTextRequest(audio_file_url=message.attachments[0].url)

    await send_voice_to_text_api_request(api_route=get_api_endpoint_url(VOICE_TO_TEXT_ENDPOINT),
                                         voice_to_text_request=voice_to_text_request,
                                         message=message
                                         )


async def send_voice_to_text_api_request(api_route: str,
                                         voice_to_text_request: VoiceToTextRequest,
                                         message: discord.Message):
    logger.info(f"Sending voice to text request payload: {voice_to_text_request.dict()}")
    reply_message = await message.reply("`awaiting bot response...`")
    response = await send_request_to_api(api_route=api_route, data=voice_to_text_request.dict())
    await reply_message.reply(
        f"{TRANSCRIBED_AUDIO_PREFIX} from user `{message.author}`:\n > {response['text']}")
    logger.info(f"VoiceToTextResponse payload received: \n {response}\n"
                f"Successfully sent voice to text request payload to API!")

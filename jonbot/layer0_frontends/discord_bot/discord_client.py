import logging

import aiohttp
import discord

from jonbot.layer0_frontends.discord_bot.event_handlers.handle_text_message import handle_text_message
from jonbot.layer0_frontends.discord_bot.event_handlers.handle_voice_memo import handle_voice_memo, \
    TRANSCRIBED_AUDIO_PREFIX

discord_client = discord.Client(intents=discord.Intents.all())

logger = logging.getLogger(__name__)

@discord_client.event
async def on_ready():
    print(f'We have logged in as {discord_client.user}')

@discord_client.event
async def on_message(message: discord.Message) -> None:
    """
    Handle a new message event from Discord.

    Parameters
    ----------
    message : discord.Message
        The message event data from Discord.
    """

    if message.author == discord_client.user and not message.content.startswith(TRANSCRIBED_AUDIO_PREFIX):
        return

    try:
        async with message.channel.typing():
                if len(message.attachments) > 0 and message.attachments[0].content_type.startswith("audio"):
                    await handle_voice_memo(message)
                else:
                    await handle_text_message(message, streaming=False)

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        logger.exception(error_message)
        await message.channel.send(f"Sorry, an error occurred while processing your request. {error_message}")



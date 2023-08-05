import logging

import discord

from jonbot.layer0_frontends.discord_bot.commands.cogs.thread_scraper_cog.server_scraper_cog import ServerScraperCog
from jonbot.layer0_frontends.discord_bot.commands.voice_command_group import voice_command_group, VOICE_RECORDING_PREFIX
from jonbot.layer0_frontends.discord_bot.event_handlers.handle_text_message import handle_text_message
from jonbot.layer0_frontends.discord_bot.event_handlers.handle_voice_memo import handle_voice_memo, \
    TRANSCRIBED_AUDIO_PREFIX

logger = logging.getLogger(__name__)

discord_bot = discord.Bot(intents=discord.Intents.all())
connections = {}


@discord_bot.listen()
async def on_ready():
    print(f'We have logged in as {discord_bot.user}')


@discord_bot.listen()
async def on_message(message: discord.Message) -> None:
    """
    Handle a new message event from Discord.

    Parameters
    ----------
    message : discord.Message
        The message event data from Discord.
    """


    if message.author == discord_bot.user:
        if not  message.content.startswith(TRANSCRIBED_AUDIO_PREFIX) and not message.content.startswith(VOICE_RECORDING_PREFIX):
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
        await message.reply(f"Sorry, an error occurred while processing your request. {error_message}")


discord_bot.add_application_command(voice_command_group)
discord_bot.add_cog(ServerScraperCog())


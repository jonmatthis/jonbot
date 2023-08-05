import logging

import discord

from jonbot.layer0_frontends.discord_bot.cogs.thread_scraper_cog.server_scraper_cog import ServerScraper
from jonbot.layer0_frontends.discord_bot.event_handlers.handle_text_message import handle_text_message
from jonbot.layer0_frontends.discord_bot.event_handlers.handle_voice_memo import handle_voice_memo, \
    TRANSCRIBED_AUDIO_PREFIX

logger = logging.getLogger(__name__)

discord_bot = discord.Bot(intents=discord.Intents.all())


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

    if message.author == discord_bot.user and not message.content.startswith(TRANSCRIBED_AUDIO_PREFIX):
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


@discord_bot.slash_command(name="scrape", description="Scrape the server into a MongoDB database")
async def scrape(ctx):
    if not ctx.author.guild_permissions.administrator:
        await ctx.respond("You do not have permission to use this command!", ephemeral=True)
        return
    await ctx.respond("Scraping server...", ephemeral=True)
    await ServerScraper().scrape_server(ctx=ctx)

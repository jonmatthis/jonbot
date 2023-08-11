import asyncio
import logging
import os

from dotenv import load_dotenv

from golembot.layer0_frontends.discord_bot.commands.voice_channel_cog import VoiceChannelCog
from golembot.layer0_frontends.discord_bot.discord_bot import DiscordBot

logging.getLogger("discord").setLevel(logging.INFO)

logger = logging.getLogger(__name__)



async def run_discord_bot_async():
    load_dotenv()
    try:
        discord_bot = DiscordBot()

    except Exception as e:
        logger.exception(f"An error occurred while starting the Discord bot: {str(e)}")
        raise

    await discord_bot.start(os.getenv("DISCORD_TOKEN"))

def run_discord_bot():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_discord_bot_async())

if __name__ == "__main__":
    run_discord_bot()


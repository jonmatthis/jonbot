import logging

import discord

from jonbot.layer0_frontends.discord_bot.cogs.voice_cog.voice_cog import VoiceCog
from jonbot.layer0_frontends.discord_bot.discord_bot import DiscordBot
from jonbot.layer1_api_interface.app import API_CHAT_URL

logger = logging.getLogger(__name__)


def run_discord_bot():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    bot = DiscordBot(api_chat_url=API_CHAT_URL,
                     intents=discord.Intents.all())
    bot.add_cog(VoiceCog())
    bot.run(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    run_discord_bot()

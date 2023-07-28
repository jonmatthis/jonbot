import logging

import discord

from jonbot.layer0_frontends.discord_bot.discord_bot import DiscordBot

logger = logging.getLogger(__name__)


def run_discord_bot():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    bot = DiscordBot(api_url="http://localhost:8000/chat",
                     intents=discord.Intents.all())
    bot.run(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    run_discord_bot()

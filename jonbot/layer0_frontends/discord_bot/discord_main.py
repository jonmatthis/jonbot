import logging
import os

from dotenv import load_dotenv

from jonbot.layer0_frontends.discord_bot.discord_bot import discord_bot

logger = logging.getLogger(__name__)


def run_discord_bot():
    load_dotenv()
    logger.info("Discord client started.")
    discord_bot.run(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    run_discord_bot()

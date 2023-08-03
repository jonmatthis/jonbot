import logging
import os

from dotenv import load_dotenv

from jonbot.layer0_frontends.discord_bot.discord_client import discord_client

logger = logging.getLogger(__name__)


def run_discord_client():
    load_dotenv()
    discord_client.run(os.getenv("DISCORD_TOKEN"))



if __name__ == "__main__":
    run_discord_client()

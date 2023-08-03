import logging
import os

import discord
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

discord_client = discord.Client(intents=discord.Intents.all())


def run_discord_client():
    load_dotenv()
    discord_client.run(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    run_discord_client()

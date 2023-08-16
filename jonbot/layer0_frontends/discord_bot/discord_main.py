import asyncio
import logging
from typing import Union

import discord

from jonbot.layer0_frontends.discord_bot.discord_bot import DiscordBot
from jonbot.models.discord_stuff.environment_config.load_discord_config import get_or_create_discord_environment_config

logging.getLogger("discord").setLevel(logging.INFO)

logger = logging.getLogger(__name__)


async def run_discord_bot_async(bot_name_or_index: Union[str, int] = 0):
    discord_environment_config = get_or_create_discord_environment_config(bot_name_or_index=bot_name_or_index)

    try:
        discord_bot = DiscordBot(environment_config= discord_environment_config,
                                 command_prefix="!",
                                 intents=discord.Intents.all())

    except Exception as e:
        logger.exception(f"An error occurred while starting the Discord bot: {str(e)}")
        raise

    await discord_bot.start(discord_environment_config.DISCORD_TOKEN)


def run_discord_bot(bot_name_or_index: Union[str, int] = 0):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_discord_bot_async(bot_name_or_index=bot_name_or_index))


if __name__ == "__main__":
    run_discord_bot()

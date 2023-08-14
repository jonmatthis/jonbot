import asyncio
import logging
from typing import Union

from jonbot.layer0_frontends.discord_bot.discord_bot import DiscordBot
from jonbot.system.environment_config.discord_config.load_discord_config import get_or_create_discord_config

logging.getLogger("discord").setLevel(logging.INFO)

logger = logging.getLogger(__name__)


async def run_discord_bot_async(bot_name_or_index: Union[str, int] = 0):
    discord_config = get_or_create_discord_config(bot_name_or_index=bot_name_or_index)

    try:
        discord_bot = DiscordBot()

    except Exception as e:
        logger.exception(f"An error occurred while starting the Discord bot: {str(e)}")
        raise

    await discord_bot.start(discord_config.DISCORD_TOKEN)


def run_discord_bot(bot_name_or_index: Union[str, int] = 0):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_discord_bot_async(bot_name_or_index=bot_name_or_index))


if __name__ == "__main__":
    run_discord_bot()

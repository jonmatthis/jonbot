import asyncio
import logging

from jonbot.layer0_frontends.discord_bot.discord_bot import DiscordBot
from jonbot.system.environment_config.discord_config.load_discord_config import DISCORD_TOKEN

logging.getLogger("discord").setLevel(logging.INFO)

import logging

logger = logging.getLogger(__name__)


async def run_discord_bot_async():
    try:
        discord_bot = DiscordBot()

    except Exception as e:
        logger.exception(f"An error occurred while starting the Discord bot: {str(e)}")
        raise

    await discord_bot.start(DISCORD_TOKEN)


def run_discord_bot():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_discord_bot_async())


if __name__ == "__main__":
    run_discord_bot()

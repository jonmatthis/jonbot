import asyncio
import logging

from jonbot.system.environment_variables import DISCORD_BOT_TOKEN
from jonbot.layer0_frontends.discord_bot.discord_bot import DiscordBot
from jonbot.layer1_api_interface.api.helpers.run_api_health_check import run_api_health_check

logging.getLogger("discord").setLevel(logging.INFO)

logger = logging.getLogger(__name__)


async def run_discord_bot_async():

    try:
        discord_bot = DiscordBot()
        await run_api_health_check()

    except Exception as e:
        logger.exception(f"An error occurred while starting the Discord bot: {str(e)}")
        raise

    await discord_bot.start(DISCORD_BOT_TOKEN)


def run_discord_bot():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_discord_bot_async())


if __name__ == "__main__":
    run_discord_bot()

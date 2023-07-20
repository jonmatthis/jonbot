import asyncio
import logging as logging
import os

from dotenv import load_dotenv

from golem_garden.backend.mongo_database.mongo_database_manager import MongoDatabaseManager
from golem_garden.frontends.discord_bot.bot import DiscordBot
from golem_garden.frontends.discord_bot.cogs.chat_cog.chat_cog import ChatCog
from golem_garden.frontends.discord_bot.cogs.thread_scraper_cog.thread_scraper_cog import ThreadScraperCog
from system.logging.configure_logging import configure_logging

configure_logging(entry_point="discord")

load_dotenv()

logger = logging.getLogger(__name__)


async def bot_main():
    mongo_database_manager = MongoDatabaseManager()
    discord_bot = DiscordBot(mongo_database=mongo_database_manager)

    discord_bot.add_cog(ChatCog(bot=discord_bot,
                                mongo_database_manager=mongo_database_manager))

    discord_bot.add_cog(ThreadScraperCog(bot=discord_bot,
                                         mongo_database_manager=mongo_database_manager))

    await discord_bot.start(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    logger.info("Starting bot...")
    asyncio.run(bot_main())

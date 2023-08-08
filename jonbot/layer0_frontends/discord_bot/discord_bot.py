import logging

import discord

from jonbot.layer0_frontends.discord_bot.commands.cogs.thread_scraper_cog.server_scraper_cog import ServerScraperCog
from jonbot.layer0_frontends.discord_bot.commands.voice_command_group import voice_command_group
from jonbot.layer0_frontends.discord_bot.event_handlers.handle_text_message import handle_text_message
from jonbot.layer0_frontends.discord_bot.event_handlers.handle_voice_memo import handle_voice_memo
from jonbot.layer0_frontends.discord_bot.utilities.should_process_message import should_process_message
from jonbot.layer3_data_layer.data_models.discord_message import DiscordMessageDocument
from jonbot.layer3_data_layer.database.mongo_database import MongoDatabaseManager

logger = logging.getLogger(__name__)

class DiscordBot(discord.Bot):
    def __init__(self, mongo_database_manager: MongoDatabaseManager):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
        self.mongo_database_manager = mongo_database_manager
        self.add_application_command(voice_command_group)
        self.add_cog(ServerScraperCog(mongo_database_manager=self.mongo_database_manager))


    @discord.Cog.listener()
    async def on_ready(self):
        print(f'We have logged in as {self.user}')


    @discord.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:

        if not should_process_message(message):
            return

        log_message_in_database(message=message)
        try:
            async with message.channel.typing():
                if len(message.attachments) > 0 and message.attachments[0].content_type.startswith("audio"):
                    # HANDLE VOICE MEMO
                    await handle_voice_memo(message)
                else:
                    # HANDLE TEXT MESSAGE
                    await handle_text_message(message,
                                                mongo_database_manager=self.mongo_database_manager,
                                              streaming=False )

        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            logger.exception(error_message)
            await message.reply(f"Sorry, an error occurred while processing your request. {error_message}")




async def log_message_in_database(message: discord.Message):
    """
    Log a message in the database.

    Parameters
    ----------
    message : discord.Message
        The message event data from Discord.
    """
    discord_message_document = DiscordMessageDocument(message=message)

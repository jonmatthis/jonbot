import asyncio
import logging

import discord

from jonbot.layer0_frontends.discord_bot.commands.voice_channel_cog import VoiceChannelCog
from jonbot.layer0_frontends.discord_bot.event_handlers.handle_text_message import handle_text_message
from jonbot.layer0_frontends.discord_bot.event_handlers.handle_voice_memo import handle_voice_memo
from jonbot.layer0_frontends.discord_bot.utilities.should_process_message import should_process_message
from jonbot.layer1_api_interface.app import get_api_endpoint_url, DATABASE_UPSERT_ENDPOINT, HEALTH_ENDPOINT
from jonbot.layer1_api_interface.send_request_to_api import send_request_to_api
from jonbot.layer3_data_layer.data_models.conversation_models import ContextRoute
from jonbot.layer3_data_layer.data_models.database_upsert_models import DatabaseUpsertRequest
from jonbot.layer3_data_layer.data_models.discord_message import DiscordMessageDocument

logger = logging.getLogger(__name__)


class DiscordBot(discord.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
        # self.add_cog(ServerScraperCog())
        self.add_cog(VoiceChannelCog())


    @discord.Cog.listener()
    async def on_ready(self):
        logger.info(f"Logged in as {self.user.name} ({self.user.id}) - checking API health...")

        while True:

            try:
                response = await send_request_to_api(api_endpoint=HEALTH_ENDPOINT,
                                                     type="GET")
                if response["status"] == "alive":
                    logger.info(f"API is alive! \n {response}")
                    break
                else:
                    logger.info(f"API is not alive yet. Waiting for 1 second before checking again.")
                    await asyncio.sleep(1)

            except Exception as e:
                logger.exception(f"An error occurred while checking API health: {str(e)}")

        self.print_pretty_startup_message_in_terminal()

    def print_pretty_startup_message_in_terminal(self):
        message = f"{self.user.name} is ready to roll!!!"
        padding = 10  # Adjust as needed
        total_length = len(message) + padding

        border = '═' * total_length
        space_padding = (total_length - len(message)) // 2

        print(f"""
        ╔{border}╗
        ║{' ' * space_padding}{message}{' ' * space_padding}║
        ╚{border}╝
        """)


    @discord.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:

        if not should_process_message(message):
            return

        await log_message_in_database(message=message)
        try:
            async with message.channel.typing():
                if len(message.attachments) > 0 and message.attachments[0].content_type.startswith("audio"):
                    # HANDLE VOICE MEMO
                    await handle_voice_memo(message)
                else:
                    # HANDLE TEXT MESSAGE
                    await handle_text_message(message,
                                              streaming=True)

        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            logger.exception(error_message)
            await message.reply(f"Sorry, an error occurred while processing your request. \n >  {error_message}")


async def log_message_in_database(message: discord.Message):
    """
    Log a message in the database.

    Parameters
    ----------
    message : discord.Message
        The message event data from Discord.
    """
    discord_message_document = await DiscordMessageDocument.from_message(message)
    database_upsert_request = DatabaseUpsertRequest(data=discord_message_document.dict(),
                                                    query={"context_route": ContextRoute.from_discord_message(
                                                        message).dict()},
                                                    collection="discord_messages",
                                                    )
    logger.info(f"Logging message in database: ContextRoute {ContextRoute.from_discord_message(message).full}")
    response = await send_request_to_api(api_route=get_api_endpoint_url(DATABASE_UPSERT_ENDPOINT),
                                         data=database_upsert_request.dict(),
                                         )
    if not response["success"]:
        logger.error(f"Failed to log message in database!! \n\n response: \n {response}")

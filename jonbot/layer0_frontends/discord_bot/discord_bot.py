import asyncio

import discord

from jonbot import get_logger
from jonbot.layer0_frontends.discord_bot.commands.cogs.memory_scraper_cog import MemoryScraperCog
from jonbot.layer0_frontends.discord_bot.commands.cogs.server_scraper_cog import ServerScraperCog
from jonbot.layer0_frontends.discord_bot.commands.cogs.voice_channel_cog import VoiceChannelCog
from jonbot.layer0_frontends.discord_bot.handlers.handle_message_responses import DiscordStreamUpdater
from jonbot.layer0_frontends.discord_bot.handlers.should_process_message import TRANSCRIBED_AUDIO_PREFIX, \
    allowed_to_reply, want_to_reply
from jonbot.layer0_frontends.discord_bot.operations.discord_database_operations import DiscordDatabaseOperations
from jonbot.layer0_frontends.discord_bot.utilities.print_pretty_terminal_message import \
    print_pretty_startup_message_in_terminal
from jonbot.layer1_api_interface.api_client.api_client import ApiClient
from jonbot.layer1_api_interface.api_client.get_or_create_api_client import get_or_create_api_client
from jonbot.layer1_api_interface.routes import CHAT_STREAM_ENDPOINT, \
    VOICE_TO_TEXT_ENDPOINT
from jonbot.models.conversation_models import ChatRequest
from jonbot.models.discord_stuff.environment_config.discord_environment import DiscordEnvironmentConfig
from jonbot.models.voice_to_text_request import VoiceToTextRequest
from jonbot.system.environment_variables import RAW_MESSAGES_COLLECTION_NAME

logger = get_logger()


async def wait_a_bit(duration: float = 1):
    await asyncio.sleep(duration)


class DiscordBot(discord.Bot):

    def __init__(self,
                 environment_config: DiscordEnvironmentConfig,
                 api_client: ApiClient = get_or_create_api_client(),

                 **kwargs
                 ):
        super().__init__(**kwargs)
        self._handling_message = False
        self._api_client = api_client
        self._database_name = f"{environment_config.BOT_NICK_NAME}_database"
        self._database_operations = DiscordDatabaseOperations(api_client=api_client,
                                                              database_name=self._database_name,
                                                              collection_name=RAW_MESSAGES_COLLECTION_NAME)
        self.add_cog(ServerScraperCog(database_operations=self._database_operations))
        self._conversations = {}

        self.add_cog(VoiceChannelCog())
        self.add_cog(MemoryScraperCog(database_name=self._database_name,
                                      api_client=api_client))

    @discord.Cog.listener()
    async def on_ready(self):
        logger.success(f"Logged in as {self.user.name} ({self.user.id})")
        print_pretty_startup_message_in_terminal(self.user.name)

    @discord.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        while self._handling_message:
            await asyncio.sleep(1)
        self._handling_message = True

        if not allowed_to_reply(message):
            return

        if not want_to_reply(message):
            logger.debug(f"Message `{message.content}` was not handled by the bot")
        else:
            try:

                async with message.channel.typing():
                    if len(message.attachments) > 0:
                        if any(attachement.content_type.startswith("audio") for attachement in message.attachments):
                            await self.handle_voice_memo(message)
                    else:
                        # HANDLE TEXT MESSAGE
                        await self.handle_text_message(message=message)

            except Exception as e:
                error_message = f"An error occurred: {str(e)}"
                logger.exception(error_message)
                await message.reply(f"Sorry, an error occurred while processing your request. \n >  {error_message}")

        asyncio.create_task(self._database_operations.upsert_message(message=message))
        self._handling_message = False

    async def handle_text_message(self,
                                  message: discord.Message,
                                  ):

        self._handling_message = True
        chat_request = ChatRequest.from_discord_message(message=message,
                                                        database_name=self._database_name)
        with message.channel.typing():
            response_tokens = await self.send_chat_api_request(chat_request=chat_request,
                                                               message=message)

    async def send_chat_api_request(self,
                                    chat_request: ChatRequest,
                                    message: discord.Message):
        updater = DiscordStreamUpdater()
        await updater.initialize_reply(message)

        async def update_discord_message_callback(token: str, updater: DiscordStreamUpdater = updater):
            logger.trace(f"Frontend received token: `{repr(token)}`")
            await updater.update_discord_reply(token)

        try:
            response_tokens = await self._api_client.send_request_to_api_streaming(endpoint_name=CHAT_STREAM_ENDPOINT,
                                                                                   data=chat_request.dict(),
                                                                                   callbacks=[
                                                                                       update_discord_message_callback])

            while not updater.done:
                await asyncio.sleep(1)

            return response_tokens
        except Exception as e:
            await updater.update_discord_reply(f"Error while streaming reply: \n >  {e}")
            raise

    async def handle_voice_memo(self,
                                message: discord.Message):
        logger.info(f"Received voice memo from user: {message.author}")
        for attachment in message.attachments:
            if attachment.content_type.startswith('audio'):
                voice_to_text_request = VoiceToTextRequest(audio_file_url=attachment.url)

                await self.send_voice_to_text_api_request(voice_to_text_request=voice_to_text_request,
                                                          message=message)

    async def send_voice_to_text_api_request(self,
                                             voice_to_text_request: VoiceToTextRequest,
                                             message: discord.Message) -> dict:
        logger.info(f"Sending voice to text request payload: {voice_to_text_request.dict()}")
        response = await self._api_client.send_request_to_api(endpoint_name=VOICE_TO_TEXT_ENDPOINT,
                                                              data=voice_to_text_request.dict())

        await message.reply(f"{TRANSCRIBED_AUDIO_PREFIX} from user `{message.author}`:\n > {response['text']}")
        logger.info(f"VoiceToTextResponse payload received: \n {response}\n"
                    f"Successfully sent voice to text request payload to API!")

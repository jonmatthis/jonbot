import asyncio
from typing import List

import discord

from jonbot import get_logger
from jonbot.layer0_frontends.discord_bot.commands.cogs.memory_scraper_cog import MemoryScraperCog
from jonbot.layer0_frontends.discord_bot.commands.cogs.server_scraper_cog import ServerScraperCog
from jonbot.layer0_frontends.discord_bot.commands.cogs.voice_channel_cog import VoiceChannelCog
from jonbot.layer0_frontends.discord_bot.handlers.handle_message_responses import DiscordMessageResponder
from jonbot.layer0_frontends.discord_bot.handlers.should_process_message import allowed_to_reply, should_reply, \
    ERROR_MESSAGE_REPLY_PREFIX_TEXT
from jonbot.layer0_frontends.discord_bot.operations.discord_database_operations import DiscordDatabaseOperations
from jonbot.layer0_frontends.discord_bot.utilities.print_pretty_terminal_message import \
    print_pretty_startup_message_in_terminal
from jonbot.layer1_api_interface.api_client.api_client import ApiClient
from jonbot.layer1_api_interface.api_client.get_or_create_api_client import get_or_create_api_client
from jonbot.layer1_api_interface.api_routes import CHAT_ENDPOINT, \
    VOICE_TO_TEXT_ENDPOINT
from jonbot.models.conversation_models import ChatRequest
from jonbot.models.discord_stuff.environment_config.discord_environment import DiscordEnvironmentConfig
from jonbot.models.voice_to_text_request import VoiceToTextRequest

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
        self._api_client = api_client
        self._database_name = f"{environment_config.BOT_NICK_NAME}_database"
        self._database_operations = DiscordDatabaseOperations(api_client=api_client,
                                                              database_name=self._database_name
                                                              )
        self.add_cog(ServerScraperCog(database_operations=self._database_operations))
        self.add_cog(VoiceChannelCog())
        self.add_cog(MemoryScraperCog(database_name=self._database_name,
                                      api_client=api_client))

    @discord.Cog.listener()
    async def on_ready(self):
        logger.success(f"Logged in as {self.user.name} ({self.user.id})")
        print_pretty_startup_message_in_terminal(self.user.name)

    @discord.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:

        if not allowed_to_reply(message):
            return

        if not should_reply(message=message,
                            bot_user_name=self.user.name):
            logger.debug(f"Message `{message.content}` was not handled by the bot: {self.user.name}")
            return

        return await self.handle_message(message=message)

    async def handle_message(self, message: discord.Message):
        messages_to_upsert = [message]
        message_responder = DiscordMessageResponder()
        with message.channel.typing():
            try:
                if len(message.attachments) > 0:
                    if any(attachment.content_type.startswith("audio") for attachment in message.attachments):
                        transcription_response_message = await self.handle_voice_recording(message=message,
                                                                                           responder=message_responder)
                        messages_to_upsert.append(transcription_response_message)

                        response_messages = await self.handle_text_message(message=transcription_response_message)
                else:
                    # HANDLE TEXT MESSAGE
                    response_messages = await self.handle_text_message(message=message)

                messages_to_upsert.extend(response_messages)

            except Exception as e:
                error_message = f"An error occurred: {str(e)}"
                logger.exception(error_message)
                await message.reply(f"{ERROR_MESSAGE_REPLY_PREFIX_TEXT} \n >  {error_message}")

        await self._database_operations.upsert_messages(messages=messages_to_upsert)

    async def handle_text_message(self,
                                  message: discord.Message,
                                  ) -> List[discord.Message]:

        chat_request = ChatRequest.from_discord_message(message=message,
                                                        database_name=self._database_name)

        updater = DiscordMessageResponder()
        await updater.initialize_reply(message)

        async def update_discord_message_callback(token: str, updater: DiscordMessageResponder = updater):
            logger.trace(f"Frontend received token: `{repr(token)}`")
            await updater.update_reply(token)

        try:
            await self._api_client.send_request_to_api_streaming(endpoint_name=CHAT_ENDPOINT,
                                                                 data=chat_request.dict(),
                                                                 callbacks=[
                                                                     update_discord_message_callback])
            while not updater.done:
                await asyncio.sleep(1)
            return updater.reply_messages

        except Exception as e:
            await updater.update_reply(f"Error while streaming reply: \n >  {e}")
            raise

    async def handle_voice_recording(self,
                                     message: discord.Message,
                                     responder: DiscordMessageResponder):
        logger.info(f"Received voice memo from user: {message.author}")
        reply_message_content = f"Transcribing audio from user `{message.author}`..."
        await responder.initialize_reply(message=message,
                                         initial_message_content=reply_message_content)
        for attachment in message.attachments:
            if attachment.content_type.startswith('audio'):
                voice_to_text_request = VoiceToTextRequest(audio_file_url=attachment.url)

                response = await self._api_client.send_request_to_api(endpoint_name=VOICE_TO_TEXT_ENDPOINT,
                                                                      data=voice_to_text_request.dict())
                reply_message_content += f"\n > File URL: {attachment.url}\n" \
                                         f"Transcribed Text:\n" \
                                         f"> {response['text']}"
                await responder.update_reply(token=reply_message_content)

                logger.info(f"VoiceToTextResponse payload received: \n {response}\n"
                            f"Successfully sent voice to text request payload to API!")

        return responder.reply_message

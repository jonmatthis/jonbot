import asyncio

import discord

from jonbot import get_logger
from jonbot.layer0_frontends.discord_bot.commands.cogs.thread_scraper_cog.server_scraper_cog import ServerScraperCog
from jonbot.layer0_frontends.discord_bot.commands.cogs.voice_channel_cog import VoiceChannelCog
from jonbot.layer0_frontends.discord_bot.handlers.handle_message_responses import DiscordStreamUpdater, \
    update_discord_message
from jonbot.layer0_frontends.discord_bot.operations.database_operations import DatabaseOperations
from jonbot.layer0_frontends.discord_bot.utilities.print_pretty_terminal_message import \
    print_pretty_startup_message_in_terminal
from jonbot.layer0_frontends.discord_bot.utilities.should_process_message import TRANSCRIBED_AUDIO_PREFIX, \
    allowed_to_reply, want_to_reply
from jonbot.layer1_api_interface.api_client.api_client import ApiClient
from jonbot.layer1_api_interface.api_client.get_or_create_api_client import get_or_create_api_client
from jonbot.layer1_api_interface.routes import CHAT_ENDPOINT, CHAT_STREAM_ENDPOINT, \
    VOICE_TO_TEXT_ENDPOINT
from jonbot.models.conversation_models import ChatRequest, ChatResponse
from jonbot.models.discord_stuff.environment_config.discord_environment import DiscordEnvironmentConfig
from jonbot.models.voice_to_text_request import VoiceToTextRequest
from jonbot.system.environment_variables import DISCORD_MESSAGES_COLLECTION_NAME

logger = get_logger()

async def wait_a_bit(duration:float=1):
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
        self._database_operations = DatabaseOperations(api_client=api_client,
                                                       database_name=self._database_name,
                                                       collection_name=DISCORD_MESSAGES_COLLECTION_NAME)
        self.add_cog(ServerScraperCog(database_operations=self._database_operations))
        self._conversations = {}

        self.add_cog(VoiceChannelCog())

    @discord.Cog.listener()
    async def on_ready(self):
        logger.success(f"Logged in as {self.user.name} ({self.user.id})")
        print_pretty_startup_message_in_terminal(self.user.name)

    @discord.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:

        if not allowed_to_reply(message):
            return

        if not want_to_reply(message):
            logger.debug(f"Message `{message.content}` was not handled by the bot")
        else:
            try:
                asyncio.create_task(self._database_operations.log_message_in_database(message=message))

                async with message.channel.typing():
                    if len(message.attachments) > 0:
                        if any(attachement.content_type.startswith("audio") for attachement in message.attachments):
                            await self.handle_voice_memo(message)
                    else:
                        # HANDLE TEXT MESSAGE
                        await self.handle_text_message(message,
                                                       streaming=True)

            except Exception as e:
                error_message = f"An error occurred: {str(e)}"
                logger.exception(error_message)
                await message.reply(f"Sorry, an error occurred while processing your request. \n >  {error_message}")

    @discord.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent, cooldown: float = 1.0):
        logger.debug(f"Received message edit: {payload.data['content']}")
        discord_message = await self.get_channel(payload.channel_id).fetch_message(payload.message_id)
        if not allowed_to_reply(discord_message):
            return

        await self._database_operations.log_message_in_database(message=discord_message)
        await asyncio.sleep(cooldown)

    async def handle_text_message(self,
                                  message: discord.Message,
                                  streaming: bool,
                                  ):

        chat_request = ChatRequest.from_discord_message(message=message,
                                                        database_name=self._database_name)

        if streaming:
            response_tokens = await self.send_chat_stream_api_request(chat_request=chat_request,
                                                                      message=message)
        else:
            response_tokens = await self.send_chat_api_request(chat_request=chat_request,
                                                               message=message)

    async def send_chat_api_request(self,
                                    chat_request: ChatRequest,
                                    message: discord.Message):
        logger.info(f"Sending chat request payload: {chat_request.dict()}")
        reply_message = await message.reply("`awaiting bot response...`")
        response = await self._api_client.send_request_to_api(endpoint_name=CHAT_ENDPOINT,
                                                              data=chat_request.dict())
        chat_response = ChatResponse(**response)
        await update_discord_message(chat_response, reply_message)
        logger.info(f"ChatRequest payload sent: \n {chat_request.dict()}\n "
                    f"ChatResponse payload received: \n {chat_response.dict()}\n"
                    f"Successfully sent chat request payload to API!")
        asyncio.create_task(self._database_operations.log_message_in_database(message=message))
        return response

    async def send_chat_stream_api_request(self,
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
            asyncio.create_task(self._database_operations.log_message_in_database(message=updater.reply_message))
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



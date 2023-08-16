import logging

import discord

from jonbot.layer0_frontends.discord_bot.commands.voice_channel_cog import VoiceChannelCog
from jonbot.layer0_frontends.discord_bot.handlers.handle_message_responses import DiscordStreamUpdater, \
    update_discord_message
from jonbot.layer0_frontends.discord_bot.utilities.get_conversation_history_from_message import \
    get_conversation_history_from_message
from jonbot.layer0_frontends.discord_bot.utilities.should_process_message import should_process_message, \
    TRANSCRIBED_AUDIO_PREFIX
from jonbot.layer1_api_interface.api_client.api_client import ApiClient
from jonbot.layer1_api_interface.api_client.get_or_create_api_client import get_or_create_api_client
from jonbot.layer1_api_interface.routes import DATABASE_UPSERT_ENDPOINT, CHAT_ENDPOINT, CHAT_STREAM_ENDPOINT, \
    VOICE_TO_TEXT_ENDPOINT
from jonbot.models.conversation_models import ContextRoute, ChatRequest, ChatResponse
from jonbot.models.database_upsert_models import DatabaseUpsertRequest
from jonbot.models.discord_stuff.discord_message import DiscordMessageDocument
from jonbot.models.discord_stuff.environment_config.discord_environment import DiscordEnvironmentConfig
from jonbot.models.voice_to_text_request import VoiceToTextRequest


from jonbot import get_logger
logger = get_logger()


class DiscordBot(discord.Bot):

    def __init__(self,
                 environment_config: DiscordEnvironmentConfig,
                 api_client:ApiClient = get_or_create_api_client(),
                 cogs: list = [VoiceChannelCog()],
                 **kwargs
                 ):
        super().__init__(**kwargs)

        # self.add_cog(ServerScraperCog())
        self._api_client = api_client
        self._database_name = f"{environment_config.BOT_NICK_NAME}_database"
        self._database_collection_name = "discord_messages"

        self._conversations = {}

        for cog in cogs:
            self.add_cog(cog)

    @discord.Cog.listener()
    async def on_ready(self):
        logger.info(f"Logged in as {self.user.name} ({self.user.id}) - checking API health...")
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

        await self.send_database_upsert_request(message=message)
        try:
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

    async def handle_text_message(self,
                                  message: discord.Message,
                                  streaming: bool,
                                  ):

        chat_request = ChatRequest.from_discord_message(message=message, )

        if streaming:
            await self.send_chat_stream_api_request(chat_request=chat_request,
                                                       message=message)
        else:
            await self.send_chat_api_request(chat_request=chat_request,
                                        message=message)

    async def send_database_upsert_request(self,
                                           message: discord.Message):
        """
        Log a message in the database.

        Parameters
        ----------
        message : discord.Message
            The message event data from Discord.
        """

        discord_message_document = await DiscordMessageDocument.from_message(message)
        database_upsert_request = DatabaseUpsertRequest(database_name=self._database_name,
                                                        collection_name=self._database_collection_name,
                                                        data=discord_message_document.dict(),
                                                        query={"context_route": ContextRoute.from_discord_message(
                                                            message).dict()},

                                                        )
        logger.info(f"Logging message in database: ContextRoute {ContextRoute.from_discord_message(message).full}")
        response = await self._api_client.send_request_to_api(endpoint_name=DATABASE_UPSERT_ENDPOINT,
                                                        data=database_upsert_request.dict(),
                                                        )
        if not response["success"]:
            logger.error(f"Failed to log message in database!! \n\n response: \n {response}")

        await self.update_conversation_history_in_database(message=message)

    async def update_conversation_history_in_database(self,
                                                      message: discord.Message):

        conversation_history = await get_conversation_history_from_message(message=message)
        upsert_request = DatabaseUpsertRequest(database_name=self._database_name,
                                               collection_name=self._database_collection_name,
                                               data=conversation_history.dict(),
                                               query={"context_route_parent": ContextRoute.from_discord_message(
                                                   message=message).parent},
                                               )

        await self._api_client.send_request_to_api(endpoint_name=DATABASE_UPSERT_ENDPOINT,
                                             data=upsert_request.dict())

        logger.info(
            f"Updated conversation history for context_route_key: {ContextRoute.from_discord_message(message=message)}")

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

    async def send_chat_stream_api_request(self,
                                                   chat_request: ChatRequest,
                                                   message: discord.Message):
        updater = DiscordStreamUpdater()
        await updater.initialize_reply(message)

        async def callback(token: str):
            logger.trace(f"Frontend received token: `{token}`")
            clean_token = token.replace("data: ", "").replace("\n\n", "")
            await updater.update_discord_reply(clean_token)

        try:
            return await self._api_client.send_request_to_api_streaming(endpoint_name=CHAT_STREAM_ENDPOINT,
                                                                  data=chat_request.dict(),
                                                                  callbacks=[callback])
        except Exception as e:
            await updater.update_discord_reply(f"Error while streaming reply: \n >  {e}")
            raise



    async def handle_voice_memo(self,
                                message: discord.Message):

        reply_message = await message.reply("Transcribing audio...")
        for attachment in message.attachments:
            if attachment.filename.startswith("audio"):
                voice_to_text_request = VoiceToTextRequest(audio_file_url=message.attachments[0].url)

                await self.send_voice_to_text_api_request(voice_to_text_request=voice_to_text_request,
                                                     message=message,
                                                     reply_message=reply_message)


    async def send_voice_to_text_api_request(self,
                                             voice_to_text_request: VoiceToTextRequest,
                                             message: discord.Message,
                                             reply_message: discord.Message):
        logger.info(f"Sending voice to text request payload: {voice_to_text_request.dict()}")
        response = await self._api_client.send_request_to_api(endpoint_name=VOICE_TO_TEXT_ENDPOINT,
                                                        data=voice_to_text_request.dict())
        tmp = reply_message.content
        await reply_message.edit(
            content=tmp + "\n" + f"{TRANSCRIBED_AUDIO_PREFIX} from user `{message.author}`:\n > {response['text']}")
        logger.info(f"VoiceToTextResponse payload received: \n {response}\n"
                    f"Successfully sent voice to text request payload to API!")

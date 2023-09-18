from typing import List, Union, Dict

import discord

from jonbot.api_interface.api_client.api_client import ApiClient
from jonbot.api_interface.api_client.get_or_create_api_client import (
    get_or_create_api_client,
)
from jonbot.api_interface.api_routes import CHAT_ENDPOINT, VOICE_TO_TEXT_ENDPOINT
from jonbot.backend.data_layer.models.conversation_models import ChatRequest
from jonbot.backend.data_layer.models.discord_stuff.environment_config.discord_environment import (
    DiscordEnvironmentConfig,
)
from jonbot.backend.data_layer.models.voice_to_text_request import VoiceToTextRequest
from jonbot.frontends.discord_bot.cogs.chat_cog import ChatCog
from jonbot.frontends.discord_bot.cogs.server_scraper_cog import ServerScraperCog
from jonbot.frontends.discord_bot.handlers.discord_message_responder import (
    DiscordMessageResponder,
)
from jonbot.frontends.discord_bot.handlers.should_process_message import (
    should_reply,
    ERROR_MESSAGE_REPLY_PREFIX_TEXT, )
from jonbot.frontends.discord_bot.operations.discord_database_operations import (
    DiscordDatabaseOperations,
)
from jonbot.frontends.discord_bot.utilities.print_pretty_terminal_message import (
    print_pretty_startup_message_in_terminal,
)
from jonbot.system.setup_logging.get_logger import get_jonbot_logger

logger = get_jonbot_logger()


class MyDiscordBot(discord.Bot):
    def __init__(
            self,
            environment_config: DiscordEnvironmentConfig,
            api_client: ApiClient = get_or_create_api_client(),
            **kwargs,
    ):
        super().__init__(**kwargs)
        self._local_message_prefix = ""
        if environment_config.IS_LOCAL:
            self._local_message_prefix = (
                f"(local - `{environment_config.BOT_NICK_NAME}`)\n"
            )

        self._api_client = api_client
        self._database_name = f"{environment_config.BOT_NICK_NAME}_database"
        self._database_operations = DiscordDatabaseOperations(
            api_client=api_client, database_name=self._database_name
        )
        self.add_cog(ServerScraperCog(database_operations=self._database_operations))
        # self.add_cog(VoiceChannelCog(bot=self))
        self.add_cog(ChatCog(bot=self))
        # self.add_cog(
        #     MemoryScraperCog(database_name=self._database_name, api_client=api_client)
        # )

    @discord.Cog.listener()
    async def on_ready(self):
        logger.success(f"Logged in as {self.user.name} ({self.user.id})")
        print_pretty_startup_message_in_terminal(self.user.name)

    @discord.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if not message.system_content == message.content:
            logger.debug(f"Message is a system message: {message.content}")
            return

        if not should_reply(message=message, bot_user_name=self.user.name, bot_id=self.user.id):
            logger.debug(
                f"Message `{message.content}` was not handled by the bot: {self.user.name}"
            )
            return

        return await self.handle_message(message=message)

    async def handle_message(self, message: discord.Message):
        messages_to_upsert = [message]
        text_to_reply_to = f"{message.author}: {message.content}"
        try:
            async with message.channel.typing():
                if len(message.attachments) > 0:
                    logger.debug(f"Message has attachments: {message.attachments}")
                    for attachment in message.attachments:
                        if "audio" in attachment.content_type:
                            audio_response_dict = await self.handle_audio_message(message=message)
                            messages_to_upsert.extend(audio_response_dict["transcriptions_messages"])
                            new_text_to_reply_to = audio_response_dict["transcription_text"]
                            text_to_reply_to += f"\n\n{new_text_to_reply_to}"
                        else:
                            new_text_to_reply_to = await self.handle_text_attachments(attachment=attachment)
                            text_to_reply_to += f"\n\n{new_text_to_reply_to}"

            response_messages = await self.handle_text_message(
                message=message,
                respond_to_this_text=text_to_reply_to
            )

            messages_to_upsert.extend(response_messages)

        except Exception as e:
            await self._send_error_response(e, messages_to_upsert)
            return

        await self._database_operations.upsert_messages(messages=messages_to_upsert)

    async def _send_error_response(self, e: Exception, messages_to_upsert):
        traceback_obj = e.__traceback__
        while traceback_obj.tb_next:
            traceback_obj = traceback_obj.tb_next

        frame = traceback_obj.tb_frame
        line_number = traceback_obj.tb_lineno
        filename = frame.f_code.co_filename

        error_message = f"Error message: \n {str(e)}"

        traceback_str = f"{filename}:{line_number}: \n ```\n{error_message}\n```"

        error_message = f"Error message: \n {str(traceback_str)}"

        # Log the error message and traceback
        logger.exception(f"Send error response:\n---\n  {error_message} \n---")

        # Send the error message and
        await messages_to_upsert[-1].reply(f"{ERROR_MESSAGE_REPLY_PREFIX_TEXT} \n >  {error_message}", )

    async def handle_text_attachments(self, attachment: discord.Attachment) -> str:
        try:
            # Try to convert to text
            text_file = await attachment.read()
            text = text_file.decode("utf-8")
            return f"\n\n{attachment.filename}:\n\n++++++\n{text}\n++++++\n"
        except UnicodeDecodeError:
            logger.warning(f"Attachment type not supported: {attachment.content_type}")
            return f"\n\n{attachment.filename}:\n\n++++++\n{attachment.url}\n++++++(Note: Could not convert this file to text)\n"

    async def handle_text_message(
            self,
            message: discord.Message,
            respond_to_this_text: str,
    ) -> List[discord.Message]:
        chat_request = ChatRequest.from_discord_message(
            message=message,
            database_name=self._database_name,
            content=respond_to_this_text,
            extra_prompts=await self.get_extra_prompts(message=message),
        )
        message_responder = DiscordMessageResponder(message_prefix=self._local_message_prefix)
        await message_responder.initialize(message=message)

        async def callback(
                token: str, responder: DiscordMessageResponder = message_responder
        ):
            logger.trace(f"FRONTEND received token: `{repr(token)}`")
            await responder.add_token_to_queue(token=token)

        try:
            await self._api_client.send_request_to_api_streaming(
                endpoint_name=CHAT_ENDPOINT,
                data=chat_request.dict(),
                callbacks=[callback],
            )
            await message_responder.shutdown()
            return await message_responder.get_reply_messages()

        except Exception as e:
            await message_responder.add_token_to_queue(
                f"  --  \n!!!\n> `Oh no! An error while streaming reply...`"
            )
            await message_responder.shutdown()
            raise

    async def handle_audio_message(self, message: discord.Message) -> Dict[str, Union[str, List[discord.Message]]]:
        logger.info(f"Received voice memo from user: {message.author}")
        try:
            reply_message_content = (
                f"Transcribing audio from user `{message.author}`\n"
            )
            responder = DiscordMessageResponder(message_prefix=self._local_message_prefix)
            await responder.initialize(
                message=message, initial_message_content=reply_message_content
            )
            for attachment in message.attachments:
                if attachment.content_type.startswith("audio"):
                    logger.debug(f"Found audio attachment: {attachment.url}")
                    reply_message_content += f"File URL: {attachment.url}\n\n"
                    await responder.add_text_to_reply_message(reply_message_content)

                    voice_to_text_request = VoiceToTextRequest(
                        audio_file_url=attachment.url
                    )

                    response = await self._api_client.send_request_to_api(
                        endpoint_name=VOICE_TO_TEXT_ENDPOINT,
                        data=voice_to_text_request.dict(),
                    )

                    transcribed_text = (
                        f"Transcribed Text:\n"
                        f"> {response['text']}\n\n"
                    )

                    await responder.add_text_to_reply_message(
                        chunk=transcribed_text,
                    )
                    await responder.shutdown()

                    logger.success(
                        f"VoiceToTextResponse payload received: \n {response}\n"
                        f"Successfully sent voice to text request payload to API!"
                    )
        except Exception as e:
            logger.exception(f"Error occurred while handling voice recording: {str(e)}")
            raise

        await responder.shutdown()
        transcriptions_messages = await responder.get_reply_messages()
        transcription_text = ""
        for message in transcriptions_messages:
            transcription_text += message.content
        return {"transcription_text": transcription_text, "transcriptions_messages": transcriptions_messages}
        # response_messages = await self.handle_text_message(
        #     message=transcriptions_messages[-1],
        #     respond_to_this_text=transcription_text,
        # )
        #
        # return transcriptions_messages + response_messages

    async def get_extra_prompts(self, message: discord.Message) -> List[str]:
        logger.debug(f"Getting extra prompts for message: {message.content}")
        prompts_from_pins = []
        prompts_from_bot_config_channel = []
        if message.channel:
            prompts_from_pins = await self.get_pinned_message_content_from_channel(channel=message.channel)
        else:
            logger.error(f"Message has no channel: {message.content}")

        if message.guild:
            prompts_from_bot_config_channel = await self.get_bot_config_channel_prompts(message)

        extra_prompts = prompts_from_pins + prompts_from_bot_config_channel
        logger.debug(f"Extra prompts: {extra_prompts}")
        return extra_prompts

    async def get_pinned_message_content_from_channel(self,
                                                      channel: discord.channel) -> List[str]:
        logger.debug(f"Getting pinned messages for channel: {channel}")
        try:
            pinned_messages = await channel.pins()
            pinned_message_content = [msg.content for msg in pinned_messages if msg.content != ""]
            logger.debug(f"Pinned messages: {pinned_message_content}")
            return pinned_message_content
        except Exception as e:
            logger.error(f"Error getting pinned messages from channel: {channel}")
            logger.exception(e)
            raise

    async def get_bot_config_channel_prompts(self,
                                             message: discord.Message,
                                             bot_config_channel_name: str = "bot-config",
                                             ) -> List[str]:
        """
        Get messages from the `bot-config` channel in the server, if it exists
        :param message:
        :param bot_config_channel_name:
        :return: List[str]
        """
        logger.debug(f"Getting extra prompts from bot-config channel")
        try:
            emoji_prompts = []
            pinned_messages = []
            for channel in message.guild.channels:
                if bot_config_channel_name in channel.name.lower():
                    logger.debug(f"Found bot-config channel")
                    pinned_messages = await self.get_pinned_message_content_from_channel(channel=channel)
                    bot_emoji_messages = await self._look_for_emoji_reaction_in_channel(channel,
                                                                                        emoji="🤖")
                    emoji_prompts = [message.content for message in bot_emoji_messages]

            extra_prompts = list(set(pinned_messages + emoji_prompts))
            logger.trace(f"Found prompts in bot-config-channel:\n {extra_prompts}\n")
            return extra_prompts
        except Exception as e:
            logger.error(f"Error getting extra prompts from bot-config channel")
            logger.exception(e)
            raise

    async def _look_for_emoji_reaction_in_channel(self,
                                                  channel: discord.TextChannel,
                                                  emoji: str) -> List[discord.Message]:
        messages = []
        async for msg in channel.history(limit=100):
            # use messages with `bot` emoji reactions as prompts
            if msg.reactions:
                for reaction in msg.reactions:
                    if str(reaction.emoji) == emoji:
                        messages.append(msg)
            logger.trace(f"Found {len(messages)} messages with {emoji} emoji reaction")
        return messages

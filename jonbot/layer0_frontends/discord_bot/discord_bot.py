import logging
import uuid

import aiohttp
import discord
from discord.ext.commands import Bot

from jonbot.layer3_data_layer.data_models.conversation_models import ChatInput, ChatResponse
from jonbot.layer3_data_layer.data_models.timestamp_model import Timestamp

logger = logging.getLogger(__name__)


class DiscordBot(Bot):
    """
    Simple Discord bot for relaying user messages to an API endpoint and then back to the user.
    """

    def __init__(self, api_chat_url: str, *args, **kwargs):
        """
        Initialize the Discord bot with the API endpoint URL.

        Parameters
        ----------
        api_chat_url : str
            The API endpoint URL to which the bot should send user messages.
        """
        super().__init__(*args, **kwargs, command_prefix="!")
        self.api_url = api_chat_url

    async def on_ready(self) -> None:
        """
        Print a message when the bot has connected to Discord.
        """
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

    async def on_message(self, message: discord.Message) -> None:
        """
        Handle a new message event from Discord.

        Parameters
        ----------
        message : discord.Message
            The message event data from Discord.
        """
        if message.author == self.user:
            return

        try:

            async with aiohttp.ClientSession() as session:
                chat_input = ChatInput(message=message.content,
                                       uuid=str(uuid.uuid4()),
                                       # metadata={'message_recieved': Timestamp().dict(),
                                       #           'discord_author_name': message.author.name,
                                       #           'discord_author_id': message.author.id,
                                       #           'discord_author_is_bot': message.author.bot,
                                       #           'discord_channel_name': message.channel.name,
                                       #           'discord_channel_id': message.channel.id,
                                       #           'discord_guild_name': message.guild.name,
                                       #           'discord_guild_id': message.guild.id,
                                       #           'discord_message_url': message.jump_url,
                                       #           'discord_message_created_at': message.created_at.isoformat(),
                                       #           },
                                       )
                logger.info(f"Sending chat input: {chat_input}")
                async with session.post(self.api_url, json=chat_input.dict()) as response:
                    if response.status == 200:
                        data = await response.json()
                        chat_response = ChatResponse(**data)
                        await message.channel.send(chat_response.message)
                    else:
                        error_message = f"Received non-200 response code: {response.status}"
                        logger.info(error_message)
                        await message.channel.send(
                            f"Sorry, I'm currently unable to process your request. {error_message}")

        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            logger.info(error_message)
            await message.channel.send(f"Sorry, an error occurred while processing your request. {error_message}")


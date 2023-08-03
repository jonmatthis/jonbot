import logging
import uuid

import aiohttp
import discord

from jonbot.layer1_api_interface.app import API_CHAT_URL
from jonbot.layer3_data_layer.data_models.conversation_models import ChatInput, ChatResponse
from jonbot.layer3_data_layer.data_models.timestamp_model import Timestamp

logger = logging.getLogger(__name__)

discord_client = discord.Client(intents=discord.Intents.all())

@discord_client.event
async def on_ready():
    print(f'We have logged in as {discord_client.user}')

@discord_client.event
async def on_message(message: discord.Message) -> None:
    """
    Handle a new message event from Discord.

    Parameters
    ----------
    message : discord.Message
        The message event data from Discord.
    """
    if message.author == discord_client.user:
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
            async with session.post(API_CHAT_URL, json=chat_input.dict()) as response:
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


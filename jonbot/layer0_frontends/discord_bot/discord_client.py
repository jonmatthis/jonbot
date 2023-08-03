import logging
import os
import uuid

import aiohttp
import discord
import requests

from jonbot.layer1_api_interface.app import API_CHAT_URL, API_VOICE_TO_TEXT_URL
from jonbot.layer3_data_layer.data_models.conversation_models import ChatInput, ChatResponse
from jonbot.layer3_data_layer.database.mongo_database import mongo_database_manager

discord_client = discord.Client(intents=discord.Intents.all())

logger = logging.getLogger(__name__)

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

            if len(message.attachments) > 0 and message.attachments[0].content_type.startswith("audio"):

                async with session.post(API_VOICE_TO_TEXT_URL, json={"audio_file_url":message.attachments[0].url}) as response:
                    if response.status == 200:
                        data = await response.json()
                        chat_response = ChatResponse(**data)
                        await message.channel.send(chat_response.message)
                        mongo_database_manager.insert_discord_message(message = message, bot_response = chat_response)
                    else:
                        error_message = f"Received non-200 response code: {response.status}"
                        logger.exception(error_message)
                        await message.channel.send(
                            f"Sorry, I'm currently unable to process your (audio transcriptiopn) request. {error_message}")

            else:

                chat_input = ChatInput(message=message.content,
                                       uuid=str(uuid.uuid4()),
                                       )
                logger.info(f"Sending chat input: {chat_input}")
                async with session.post(API_CHAT_URL, json=chat_input.dict()) as response:
                    if response.status == 200:
                        data = await response.json()
                        chat_response = ChatResponse(**data)
                        await message.channel.send(chat_response.message)
                        mongo_database_manager.insert_discord_message(message = message, bot_response = chat_response)
                    else:
                        error_message = f"Received non-200 response code: {response.status}"
                        logger.exception(error_message)
                        await message.channel.send(
                            f"Sorry, I'm currently unable to process your request. {error_message}")

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        logger.exception(error_message)
        await message.channel.send(f"Sorry, an error occurred while processing your request. {error_message}")



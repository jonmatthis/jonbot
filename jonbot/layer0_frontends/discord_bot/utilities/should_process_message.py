import discord

from jonbot import get_logger
from jonbot.models.discord_stuff.environment_config.load_discord_config import get_or_create_discord_environment_config

logger = get_logger()

VOICE_RECORDING_PREFIX = "Finished! Recorded audio for"
TRANSCRIBED_AUDIO_PREFIX = "Transcribed audio for"


def check_if_mentioned(message: discord.Message) -> bool:
    if message.author in message.mentions:
        return True


def check_if_bot(message: discord.Message) -> bool:
    # If it's a bot message and doesn't start with the expected prefixes, return False
    return message.author.bot


def check_if_transcribed_audio_message(message: discord.Message) -> bool:
    return (message.content.startswith(TRANSCRIBED_AUDIO_PREFIX) or
            message.content.startswith(VOICE_RECORDING_PREFIX))


def want_to_reply(message: discord.Message) -> bool:
    if not allowed_to_reply(message):
        return False

    if check_if_mentioned(message):
        return True

    if check_if_transcribed_audio_message(message):
        return True

    if check_if_bot(message):
        return False

    return True


def allowed_to_reply(message: discord.Message) -> bool:
    discord_config = get_or_create_discord_environment_config()

    # Handle DMs
    if message.channel.type == discord.ChannelType.private:
        return discord_config.DIRECT_MESSAGES_ALLOWED

    # Handle server messages
    server_data = None
    for server_name, details in discord_config.SERVERS_DETAILS.items():
        if message.guild.id == details['SERVER_ID']:
            server_data = details
            break

    if not server_data:
        logger.warning(
            f"Message received from server {message.guild.id} which is not in the list of allowed servers :O")
        return False

    allowed_categories = server_data.get("ALLOWED_CATEGORY_IDS", [])
    if allowed_categories == ["ALL"]:
        return True

    if message.channel.category_id in allowed_categories:
        return True

    allowed_channels = server_data.get("ALLOWED_CHANNEL_IDS", [])
    if allowed_channels == ["ALL"]:
        return True
    if message.channel.id not in allowed_channels:
        return False

    return True

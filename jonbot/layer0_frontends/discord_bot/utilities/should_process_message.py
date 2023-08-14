import discord

from jonbot.layer0_frontends.discord_bot.commands.voice_channel_cog import VOICE_RECORDING_PREFIX
from jonbot.layer0_frontends.discord_bot.event_handlers.handle_voice_memo import TRANSCRIBED_AUDIO_PREFIX
from jonbot.system.environment_config.discord_config.load_discord_config import SERVERS_DETAILS, DIRECT_MESSAGES_ALLOWED

import logging
logger = logging.getLogger(__name__)
def should_process_message(message) -> bool:
    # If it's a bot message and doesn't start with the expected prefixes, return False
    if message.author.bot:
        if not (message.content.startswith(TRANSCRIBED_AUDIO_PREFIX) or
                message.content.startswith(VOICE_RECORDING_PREFIX)):
            return False

    # Handle DMs
    if message.channel.type == discord.ChannelType.private:
        return DIRECT_MESSAGES_ALLOWED

    # Handle server messages
    server_data = None
    for server_name, details in SERVERS_DETAILS.items():
        if message.guild.id == details['server_id']:
            server_data = details
            break

    if not server_data:
        logger.warning(f"Message received from server {message.guild.id} which is not in the list of allowed servers :O")
        return False

    allowed_channels = server_data.get("allowed_channel_ids", [])
    if allowed_channels == ["ALL"]:
        return True
    if message.channel.id not in allowed_channels:
        return False

    return True
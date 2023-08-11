import os

import discord
from dotenv import load_dotenv

from golembot.layer0_frontends.discord_bot.commands.voice_channel_cog import VOICE_RECORDING_PREFIX
from golembot.layer0_frontends.discord_bot.event_handlers.handle_voice_memo import TRANSCRIBED_AUDIO_PREFIX


def get_allowed_chanels():
    load_dotenv()
    allowed_channels = os.getenv("ALLOWED_CHANNELS")
    if allowed_channels is None:
        raise ValueError("ALLOWED_CHANNELS environment variable not set.")

    if allowed_channels == "ALL":
        return allowed_channels
    else:
        return [int(channel_id) for channel_id in allowed_channels.split(",")]


DIRECT_MESSAGES_ALLOWED = True


def should_process_message(message)->bool:
    allowed_channels = get_allowed_chanels()
    if not allowed_channels == "ALL":
        if not message.channel.id in allowed_channels:
            return False

    if not DIRECT_MESSAGES_ALLOWED and message.channel.type == discord.ChannelType.private:
        return False

    if message.author.bot:
        if not any([message.content.startswith(TRANSCRIBED_AUDIO_PREFIX),
                    message.content.startswith(VOICE_RECORDING_PREFIX)]):
            return False

    return True
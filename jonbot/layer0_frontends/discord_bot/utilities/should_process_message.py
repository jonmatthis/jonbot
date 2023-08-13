import discord

from jonbot.layer0_frontends.discord_bot.commands.voice_channel_cog import VOICE_RECORDING_PREFIX
from jonbot.layer0_frontends.discord_bot.event_handlers.handle_voice_memo import TRANSCRIBED_AUDIO_PREFIX
from jonbot.system.environment_variables import DIRECT_MESSAGES_ALLOWED, ALLOWED_CHANNELS


def should_process_message(message) -> bool:
    if not ALLOWED_CHANNELS == "ALL":
        if not message.channel.id in ALLOWED_CHANNELS:
            return False

    if not DIRECT_MESSAGES_ALLOWED and message.channel.type == discord.ChannelType.private:
        return False

    if message.author.bot:
        if not any([message.content.startswith(TRANSCRIBED_AUDIO_PREFIX),
                    message.content.startswith(VOICE_RECORDING_PREFIX)]):
            return False

    return True

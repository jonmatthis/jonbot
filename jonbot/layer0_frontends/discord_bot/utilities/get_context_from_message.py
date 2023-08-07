import logging

import discord

from jonbot.layer3_data_layer.data_models.conversation_models import ConversationalContext, Speaker
from jonbot.layer3_data_layer.data_models.timestamp_model import Timestamp

logger = logging.getLogger(__name__)



def get_context_route_from_discord_message(message: discord.Message) -> str:
    frontend: str = 'discord'
    server: str = f"{message.guild.name}_{message.guild.id}" if message.guild else 'DirectMessage'
    channel: str = f"{message.channel.name}_{message.channel.id}" if message.channel.type != discord.ChannelType.private else f"DirectMessage_{message.channel.id}"

    if determine_if_discord_message_is_from_a_thread(message):
        context_route = f"frontend-{frontend}/server-{server}/channel-{channel}/thread-{message.thread.name}/messages/message_id-{message.id}"
    else:
        context_route = f"frontend-{frontend}/server-{server}/channel-{channel}/messages/message_id-{message.id}"

    return context_route


def determine_if_discord_message_is_from_a_thread(message) -> bool:
    return True if message.thread else False


def get_context_description_from_discord_message(message: discord.Message) -> str:
    """Get the context description based on the given message."""

    frontend = "You are having a conversation via the Discord frontend."
    server = ""

    # Direct message context
    if not message.guild:
        server = f"It is happening via direct message with {message.author.name}"
        return f"{frontend} {server}"

    channel = f"It is happening in the channel: {message.channel.name} with Description: {message.channel.topic or 'None'}"

    # Thread context
    if determine_if_discord_message_is_from_a_thread(message):
        thread = f"It is happening in the thread: {message.thread.name}"
        return f"{frontend} {server} {channel} {thread}"

    return f"{frontend} {server} {channel}"


def get_conversational_context_from_discord_message(message: discord.Message) -> ConversationalContext:
    return ConversationalContext(context_route= get_context_route_from_discord_message(message),
                                 context_description=get_context_description_from_discord_message(message),
                                 timestamp=Timestamp.from_datetime(message.created_at),)


def get_speaker_from_discord_message(message: discord.Message):
    speaker = Speaker(name=str(message.author),
                      id=message.author.id,
                      type="Bot" if message.author.bot else "Human")

    return speaker

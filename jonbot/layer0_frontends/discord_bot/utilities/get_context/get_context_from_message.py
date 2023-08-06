import logging
from typing import Tuple

import discord

from jonbot.layer3_data_layer.data_models.conversation_models import ConversationalContext, Speaker
from jonbot.layer3_data_layer.data_models.timestamp_model import Timestamp

logger = logging.getLogger(__name__)


def get_context_route_from_message(message: discord.Message) -> str:
    in_thread = determine_if_message_is_happening_in_a_thread(message)
    try:
        if not message.guild:
            context_route = f"frontend|discord/direct_messages||{message.channel.recipient.name}/message||{message.id}"
        else:
            if in_thread:
                context_route = f"frontend|discord/server||{message.guild.name}/channel||{message.channel.name}/threads/{message.thread.name}/message_id||{message.id}"
            else:
                context_route = f"frontend|discord/server||{message.guild.name}/channel||{message.channel.name}/messages/message_id||{message.id}"
    except Exception as e:
        logger.info(f"Failed to get context route for message: {message.id}")
        logger.exception(e)
        context_route = 'unknown'

    return context_route


def determine_if_message_is_happening_in_a_thread(message) -> bool:
    return True if message.thread else False


def get_context_description_from_message(message: discord.Message) -> str:
    """Get the context description based on the given message."""

    frontend = "You are having a conversation via the Discord frontend."
    server = ""

    # Direct message context
    if not message.guild:
        server = f"It is happening via direct message with {message.channel.recipient.name}"
        return f"{frontend} {server}"

    channel = f"It is happening in the channel: {message.channel.name} with Description: {message.channel.topic or 'None'}"

    # Thread context
    if determine_if_message_is_happening_in_a_thread(message):
        thread = f"It is happening in the thread: {message.thread.name}"
        return f"{frontend} {server} {channel} {thread}"

    return f"{frontend} {server} {channel}"


def get_conversational_context_from_message(message: discord.Message) -> ConversationalContext:
    return ConversationalContext(context_route=get_context_route_from_message(message),
                                 context_description=get_context_description_from_message(message),
                                 timestamp=Timestamp(date_time=message.created_at))

def get_speaker_from_message(message: discord.Message):
    speaker = Speaker(name=str(message.author),
                      id=message.author.id,
                      type="Bot" if message.author.bot  else "Human")

    return speaker


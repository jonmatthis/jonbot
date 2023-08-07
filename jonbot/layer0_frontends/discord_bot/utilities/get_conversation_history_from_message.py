import discord

from jonbot.layer0_frontends.discord_bot.utilities.get_context_from_message import \
    get_speaker_from_discord_message, get_context_route_from_discord_message
from jonbot.layer3_data_layer.data_models.conversation_models import ConversationHistory, ChatMessage
from jonbot.layer3_data_layer.data_models.timestamp_model import Timestamp


async def get_conversation_history_from_message(message: discord.Message) -> ConversationHistory:
    """
    Fetch the conversation history from a given message.

    Args:
        message (discord.Message): The message from which history needs to be fetched.

    Returns:
        ConversationHistory: An object containing the conversation history.
    """

    context_route = get_context_route_from_discord_message(message)
    conversation_history = ConversationHistory(context_route=context_route)

    # Define a helper function to add a message to the history

    def add_to_history(msg: discord.Message):
        speaker = get_speaker_from_discord_message(msg)

        chat_message = ChatMessage(message=msg.content,
                                   speaker=speaker,
                                   timestamp=Timestamp.from_datetime(message.created_at))

        conversation_history.add_message(chat_message)

    # Check if the message is in a thread
    if message.thread:
        async for msg in message.thread.history(limit=None, oldest_first=True):
            if msg.content:
                add_to_history(msg)
    else:
        async for msg in message.channel.history(limit=None, oldest_first=True):
            if msg.content:
                add_to_history(msg)

    return conversation_history

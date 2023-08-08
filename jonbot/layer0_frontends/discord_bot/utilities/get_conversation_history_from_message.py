import discord

from jonbot.layer0_frontends.discord_bot.utilities.get_context_from_message import \
    get_speaker_from_discord_message, get_context_route_from_discord_message
from jonbot.layer3_data_layer.data_models.conversation_models import ConversationHistory, ChatMessage
from jonbot.layer3_data_layer.data_models.timestamp_model import Timestamp


async def get_conversation_history_from_message(message: discord.Message,
                                                message_limit: int = 100) -> ConversationHistory:
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

    # Check if the message is in a thread
    if message.thread:
        message_history = message.thread.history(limit=message_limit, oldest_first=False)
    else:
        message_history = message.channel.history(limit=message_limit, oldest_first=False)

    async for msg in message_history:
        if msg.content:
            conversation_history.add_message(chat_message=ChatMessage(message=msg.content,
                                                                      speaker=get_speaker_from_discord_message(msg),
                                                                      timestamp=Timestamp.from_datetime(
                                                                          msg.created_at)))

    return conversation_history

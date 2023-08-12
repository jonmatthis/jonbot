import discord

from jonbot.models.conversation_models import ConversationHistory, ChatMessage


async def get_conversation_history_from_message(message: discord.Message,
                                          message_limit: int = 100) -> ConversationHistory:

    # Check if the message is in a thread
    if message.thread:
        message_history = message.thread.history(limit=message_limit, oldest_first=False)
    else:
        message_history = message.channel.history(limit=message_limit, oldest_first=False)

    conversation_history = ConversationHistory()

    async for msg in message_history:
        if msg.content:
            conversation_history.add_message(chat_message=ChatMessage.from_discord_message(message=msg))

    return conversation_history

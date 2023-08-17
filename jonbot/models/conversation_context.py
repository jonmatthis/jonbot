from typing import Union

import discord
from pydantic import BaseModel

from jonbot.models.timestamp_model import Timestamp

DIRECT_MESSAGE_CHANNEL_DESCRIPTION = """
This is a direct message channel between you and the human.

NOTE THAT CONVERSATIONS IN THIS CHANNEL ARE STILL LOGGED AND MAY BE USED AS PART OF THE CONTEXT OF CONVERSATIONS IN THE BOTS HOME SERVER
"""


class ConversationContext(BaseModel):
    context_description: str = "unknown"
    timestamp: Union[Timestamp, str] = "unknown"

    @classmethod
    def from_discord_message(cls, message: discord.Message):
        context_description = cls.get_context_description(message)

        return cls(context_description=context_description,
                   timestamp=Timestamp.from_datetime(message.created_at)
                   )

    @staticmethod
    def get_context_description(message: discord.Message):
        if message.channel.type.name == 'private':
            context_description = DIRECT_MESSAGE_CHANNEL_DESCRIPTION
        else:
            if "thread" in message.channel.type.name:
                context_description = f"Thread {message.channel.name} " \
                                      f"in channel {message.channel.parent.name}" \
                                      f" in server {message.guild.name}"

            elif message.channel.topic:
                context_description = message.channel.topic

            else:
                context_description = f"Channel {message.channel.name} in server {message.guild.name}"
        return context_description

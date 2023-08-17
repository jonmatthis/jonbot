from typing import Optional, Union

import discord
from pydantic import BaseModel

from jonbot.models.timestamp_model import Timestamp


class ContextRoute(BaseModel):
    """How to grab this context route from the database"""
    frontend: str
    server: str
    channel: str
    thread: Optional[str] = None

    @classmethod
    def from_discord_message(cls, message: discord.Message):
        frontend = 'discord'
        server = f"{message.guild.name}_{message.guild.id}" if message.guild else 'DirectMessage'

        if message.channel.type == discord.ChannelType.private:
            thread = None
            channel = f"DirectMessage_{message.channel.id}"
        elif "thread" in message.channel.type.name:
            thread = f"{message.channel.name}_{message.channel.id}"
            channel = f"{message.channel.parent.name}_{message.channel.parent.id}" if message.channel.parent else None
        else:
            thread = None
            channel = f"{message.channel.name}_{message.channel.id}"
        return cls(frontend=frontend,
                   server=server,
                   channel=channel,
                   thread=thread,
                   )

    @property
    def as_path(self):
        if self.thread:
            return f"frontend-{self.frontend}/server-{self.server}/channel-{self.channel}/thread-{self.thread}/"
        else:
            return f"frontend-{self.frontend}/server-{self.server}/channel-{self.channel}/messages/"

    @classmethod
    def dummy(cls, text: str = "unknown"):
        return cls(frontend=text,
                   server=text,
                   channel=text,
                   thread=text,
                   )


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

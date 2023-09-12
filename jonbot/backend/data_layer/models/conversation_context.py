import discord
from pydantic import BaseModel

from jonbot.backend.data_layer.models.timestamp_model import Timestamp

DIRECT_MESSAGE_CHANNEL_DESCRIPTION = """
This is a direct message channel between you and the human.

NOTE THAT CONVERSATIONS IN THIS CHANNEL ARE STILL LOGGED AND MAY BE USED AS PART OF THE CONTEXT OF CONVERSATIONS IN THE BOTS HOME SERVER
"""


class ConversationContextDescription(BaseModel):
    text: str

    @classmethod
    def from_discord_message(cls, message: discord.Message):
        context_description = cls._get_context_description(message)
        return cls(text=context_description)

    @staticmethod
    def _get_context_description(message: discord.Message):
        if message.channel.type.name == "private":
            context_description = DIRECT_MESSAGE_CHANNEL_DESCRIPTION
        else:
            context_description = (f"This conversation is happening in a Discord with a user named: `{message.author}` "
                                   f"in a server named: `{message.guild.name}` \n")

            if "thread" in message.channel.type.name:

                if message.channel.parent.topic:
                    context_description += f" with the topic description: `{message.channel.parent.topic}`\n"

                context_description += f"in a Thread named `{message.channel.name}` "

            else:
                if message.channel.topic:
                    context_description += f" with the topic description: `{message.channel.topic}`\n"

                context_description += f"in channel named `{message.channel.name}`\n"

                context_description += f"The local time/date of the sender isstr({Timestamp.from_datetime(message.created_at)})"

        return context_description

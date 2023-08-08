import uuid
from typing import Union, Optional, List, Literal

import discord
from pydantic import BaseModel, Field

from jonbot.layer3_data_layer.data_models.timestamp_model import Timestamp


class ContextRoute(BaseModel):
    full: str
    parent: str
    frontend: str
    server: str
    channel: str
    thread: Optional[str] = None
    message_id: int = None

    @classmethod
    def from_discord_message(cls,
                             message: discord.Message,
                             parent_route_only: bool = False,
                             ):
        frontend = 'discord'
        server = f"{message.guild.name}_{message.guild.id}" if message.guild else 'DirectMessage'
        channel = f"{message.channel.name}_{message.channel.id}" if message.channel.type != discord.ChannelType.private else f"DirectMessage_{message.channel.id}"
        thread = f"{message.thread.name}_{message.thread.id}" if message.thread else None
        message_id = message.id

        if thread:
            parent = f"frontend-{frontend}/server-{server}/channel-{channel}/thread-{thread}/"
        else:
            parent = f"frontend-{frontend}/server-{server}/channel-{channel}/messages/"


        if parent_route_only:
            full = parent
        else:
            full = f"{parent}message-{message_id}/"


        return cls(full=full,
                   parent=parent,
                   frontend=frontend,
                   server=server,
                   channel=channel,
                   thread=thread,
                   message_id=message_id if not parent_route_only else 0,
                   )


DIRECT_MESSAGE_CHANNEL_DESCRIPTION = """
This is a direct message channel between you and the human.

NOTE THAT CONVERSATIONS IN THIS CHANNEL ARE STILL LOGGED AND MAY BE USED AS PART OF THE CONTEXT OF CONVERSATIONS IN THE BOTS HOME SERVER
"""


class ConversationalContext(BaseModel):
    context_route: ContextRoute
    context_description: str
    timestamp: Timestamp

    @classmethod
    def from_discord_message(cls, message: discord.Message):
        return cls(context_route=ContextRoute.from_discord_message(message=message),
                   context_description=DIRECT_MESSAGE_CHANNEL_DESCRIPTION if message.channel.type.name == 'private' else message.channel.topic,
                   timestamp=Timestamp.from_datetime(message.created_at)
                   )


class ChatInput(BaseModel):
    message: str
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict = {}


class ChatResponse(BaseModel):
    message: str
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict = {}


class Speaker(BaseModel):
    name: str
    id: Optional[Union[int, str]]
    type: Literal['bot', 'human']

    @classmethod
    def from_discord_message(cls, message: discord.Message):
        return cls(name=message.author.name,
                   id=message.author.id,
                   type='bot' if message.author.bot else 'human')


class ChatMessage(BaseModel):
    message: str
    speaker: Speaker
    timestamp: Timestamp
    context_route: ContextRoute
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict = {}

    @classmethod
    def from_discord_message(cls, message: discord.Message):
        return cls(message=message.content,
                   speaker=Speaker.from_discord_message(message=message),
                   timestamp=Timestamp.from_datetime(message.created_at),
                   context_route=ContextRoute.from_discord_message(message=message),
                   )


class ConversationHistory(BaseModel):
    history: List[ChatMessage] = Field(default_factory=list)

    def add_message(self, chat_message: ChatMessage):
        self.history.append(chat_message)

    def get_all_messages(self) -> List[ChatMessage]:
        return self.history

    def __len__(self):
        return len(self.history)


class ChatRequestConfig(BaseModel):
    dummy: str = "hi:D"


class ChatRequest(BaseModel):
    chat_input: ChatInput
    conversational_context: ConversationalContext
    config: ChatRequestConfig = ChatRequestConfig()
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))

    @classmethod
    def from_discord_message(cls, message):
        return cls(chat_input=ChatInput(message=message.content),
                   conversational_context=ConversationalContext.from_discord_message(message=message)
                   )

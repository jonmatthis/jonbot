import uuid
from typing import Union, Optional, List, Literal

import discord
from pydantic import BaseModel, Field

from jonbot.models.ai_chatbot_models import VectorStoreMemoryConfig
from jonbot.models.conversation_context import ConversationContext
from jonbot.models.context_route import ContextRoute
from jonbot.models.discord_stuff.discord_message import DiscordMessageDocument
from jonbot.models.timestamp_model import Timestamp


class ChatInput(BaseModel):
    message: str
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict = {}


class ChatResponse(BaseModel):
    text: str
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict = {}

    @classmethod
    def from_tokens(cls, tokens: List[str]):
        return cls(text=''.join(tokens),
                   metadata={'tokens': tokens})


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
    def from_discord_message(cls, message: Union[discord.Message, DiscordMessageDocument]):
        if isinstance(message, DiscordMessageDocument):
            context_route = message.context_route
        elif isinstance(message, discord.Message):
            context_route = ContextRoute.from_discord_message(message=message)
        else:
            raise ValueError(f"Cannot create ChatMessage from {type(message)}")
        return cls(message=message.content,
                   speaker=Speaker.from_discord_message(message=message),
                   timestamp=Timestamp.from_datetime(message.created_at),
                   context_route=context_route,
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
    vector_store_memory_config: VectorStoreMemoryConfig = VectorStoreMemoryConfig()


class ChatRequest(BaseModel):
    chat_input: ChatInput
    database_name: str
    context_route: ContextRoute
    conversation_context: ConversationContext
    config: ChatRequestConfig = ChatRequestConfig()
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))

    @classmethod
    def from_text(cls,
                  text: str,
                  timestamp: Timestamp,
                  database_name: str,
                  context_description: str = "unknown",
                  context_route: ContextRoute = ContextRoute.dummy(dummy_text="dummy"),
                  **kwargs
                  ):
        return cls(chat_input=ChatInput(message=text),
                   database_name=database_name,
                   context_route=context_route,
                   conversation_context=ConversationContext(timestamp=timestamp,
                                                            context_description=context_description,
                                                            ),
                   **kwargs
                   )

    @classmethod
    def from_discord_message(cls,
                             message: discord.Message,
                             database_name: str,
                             **kwargs):
        return cls.from_text(text=message.content,
                             timestamp=Timestamp.from_datetime(message.created_at),
                             database_name=database_name,
                             context_route=ContextRoute.from_discord_message(message),
                             context_description=ConversationContext.get_context_description(message),
                             **kwargs)

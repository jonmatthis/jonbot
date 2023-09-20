import uuid
from typing import Union, Optional, List, Literal, Dict, Any

import discord
from pydantic import BaseModel, Field

from jonbot.backend.data_layer.models.ai_chatbot_models import VectorStoreMemoryConfig
from jonbot.backend.data_layer.models.context_route import ContextRoute
from jonbot.backend.data_layer.models.conversation_context import ConversationContextDescription
from jonbot.backend.data_layer.models.discord_stuff.discord_message_document import DiscordMessageDocument
from jonbot.backend.data_layer.models.timestamp_model import Timestamp


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
        return cls(text="".join(tokens), metadata={"tokens": tokens})


class Speaker(BaseModel):
    name: str
    id: Optional[Union[int, str]]
    type: Literal["bot", "human"]

    @classmethod
    def from_discord_message(cls, message: discord.Message):
        return cls(
            name=message.author.name,
            id=message.author.id,
            type="bot" if message.author.bot else "human",
        )


class ChatMessage(BaseModel):
    content: str
    speaker: Speaker
    timestamp: Timestamp
    context_route: ContextRoute
    original_message_document: Optional[DiscordMessageDocument] = None
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict = {}

    @classmethod
    async def from_discord_message(cls, message: discord.Message):
        return cls.from_discord_message_document(
            await DiscordMessageDocument.from_discord_message(message)
        )

    @classmethod
    def from_discord_message_document(cls, message_document: DiscordMessageDocument):
        return cls(
            content=message_document.content,
            speaker=Speaker(
                name=message_document.author,
                id=message_document.author_id,
                type="bot" if message_document.is_bot else "human",
            ),
            timestamp=message_document.timestamp,
            context_route=message_document.context_route_object,
            original_message_document=message_document,
        )


class MessageHistory(BaseModel):
    history: List[ChatMessage] = Field(default_factory=list)

    def add_message(self, chat_message: ChatMessage):
        self.history.append(chat_message)
        self.history.sort(
            key=lambda chat_message: chat_message.timestamp.utc
        )  # Sorting the history by timestamp

    def get_all_messages(self) -> List[ChatMessage]:
        return self.history

    def __len__(self):
        return len(self.history)


class ChatRequestConfig(BaseModel):
    vector_store_memory_config: VectorStoreMemoryConfig = VectorStoreMemoryConfig()
    limit_messages: Optional[int] = 20
    temperature: Optional[float] = 0.9
    model_name: Optional[str] = "gpt-4"
    extra_prompts: Optional[List[str]] = None
    memory_messages: Optional[List[DiscordMessageDocument]] = None

    @classmethod
    def from_kwargs(cls, kwargs: Dict[str, Any]):
        build_dict = {}
        for key, value in kwargs.items():
            if key in ChatRequestConfig.__fields__:
                build_dict[key] = value
        return cls(**build_dict)


class ChatRequest(BaseModel):
    user_id: Union[int, str]
    message_id: int
    reply_message_id: int
    chat_input: ChatInput
    database_name: str
    context_route: ContextRoute
    conversation_context_description: ConversationContextDescription
    config: ChatRequestConfig
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))

    @classmethod
    def from_text(
            cls,
            user_id: Union[int, str],
            message_id: int,
            reply_message_id: int,
            text: str,
            database_name: str,
            context_description_text: str,
            config: ChatRequestConfig,
            timestamp: Timestamp,
            context_route: ContextRoute  # = ContextRoute.dummy(dummy_text="dummy"),
    ):
        return cls(
            user_id=user_id,
            message_id=message_id,
            reply_message_id=reply_message_id,
            chat_input=ChatInput(message=text),
            database_name=database_name,
            context_route=context_route,
            conversation_context_description=ConversationContextDescription(text=context_description_text),
            config=config,
            timestamp=timestamp,
        )

    @classmethod
    def from_discord_message(
            cls,
            message: discord.Message,
            reply_message: discord.Message,
            database_name: str,
            content: str,
            config: ChatRequestConfig,
    ):
        return cls.from_text(
            user_id=message.author.id,
            message_id=message.id,
            reply_message_id=reply_message.id,
            text=content,
            timestamp=Timestamp.from_datetime(message.created_at),
            database_name=database_name,
            context_route=ContextRoute.from_discord_message(message),
            context_description_text=ConversationContextDescription.from_discord_message(message).text,
            config=config,
        )

    @classmethod
    def from_discord_message_document(
            cls,
            message_document: DiscordMessageDocument, database_name: str, **kwargs
    ):
        return cls.from_text(
            text=message_document.content,
            timestamp=message_document.timestamp,
            database_name=database_name,
            context_route=message_document.context_route,
            **kwargs
        )

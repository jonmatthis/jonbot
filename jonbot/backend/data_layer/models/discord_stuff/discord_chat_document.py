from typing import List, Optional, Dict, Any

import discord
from pydantic import BaseModel, Field

from jonbot.backend.data_layer.models.context_route import ContextRoute
from jonbot.backend.data_layer.models.conversation_context import ConversationContextDescription
from jonbot.backend.data_layer.models.conversation_models import Speaker, ChatCouplet
from jonbot.backend.data_layer.models.discord_stuff.discord_message_document import DiscordMessageDocument
from jonbot.backend.data_layer.models.timestamp_model import Timestamp
from jonbot.system.setup_logging.get_logger import get_jonbot_logger

logger = get_jonbot_logger()


class DiscordChatDocument(BaseModel):
    messages: List[DiscordMessageDocument]
    couplets: Optional[List[ChatCouplet]]
    created_at: Timestamp
    last_accessed: Timestamp
    owner_id: int
    owner_name: str
    server_name: str
    server_id: int
    category_name: str
    category_id: int
    channel_name: str
    channel_id: int
    thread_name: str
    thread_id: int
    speakers: List[Speaker]
    jump_url: str
    parent_message_id: int
    context_description: str
    context_route: ContextRoute
    context_route_full_path: str
    context_route_as_friendly_dict: str
    context_route_as_tree_path: List[str]
    context_route_as_friendly_tree_path: List[str]
    query: dict

    as_text: str = ""

    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @classmethod
    async def build(cls,
                    chat_id: int,
                    parent_message: discord.Message,
                    messages: List[discord.Message]):

        message_documents = [
            await DiscordMessageDocument.from_discord_message(message)
            for message in messages
        ]
        cls._validate_messages(message_documents=message_documents)

        speakers = await cls.get_unique_speakers(messages)

        context_route = ContextRoute.from_discord_message(message=messages[0])

        instance = cls(
            messages=message_documents,
            couplets=cls.to_couplets(message_documents),
            created_at=Timestamp.from_datetime(parent_message.created_at),
            last_accessed=Timestamp.now(),
            owner_id=parent_message.author.id,
            owner_name=parent_message.author.name,
            jump_url=parent_message.jump_url,
            parent_message_id=parent_message.id,
            speakers=speakers,
            context_description=ConversationContextDescription.from_discord_message(parent_message).text,
            context_route=context_route,
            context_route_full_path=context_route.full_path,
            context_route_as_friendly_dict=context_route.friendly_path,
            context_route_as_tree_path=context_route.as_tree_path,
            context_route_as_friendly_tree_path=context_route.as_friendly_tree_path,
            query={"chat_id": chat_id},
            metadata={},
            **context_route.as_flat_dict,
        )
        instance.as_text = instance._to_text()
        return instance

    def _to_text(self):
        text = ""
        if self.couplets is not None:
            for couplet in self.couplets:
                text += f"[{couplet.as_text}],\n\n"
        else:
            for message in self.messages:
                text += f"[{message.content}],\n\n"
        return text

    @classmethod
    async def get_unique_speakers(cls, messages: List[discord.Message]) -> List[Speaker]:
        all_speakers = [Speaker.from_discord_message(message).dict() for message in messages]
        speakers = []
        for speaker in all_speakers:
            if speaker not in speakers:
                speakers.append(speaker)
        return speakers

    @classmethod
    def _validate_messages(cls, message_documents: List[DiscordMessageDocument]):
        thread_id = message_documents[0].thread_id
        for message in message_documents:
            if message.thread_id != thread_id:
                raise Exception("Messages must have the same thread id")

    @staticmethod
    def to_couplets(messages: List[DiscordMessageDocument]) -> List[ChatCouplet]:
        couplets = []
        ai_messages = [message for message in messages if message.is_bot]
        human_messages = [message for message in messages if not message.is_bot]

        ai_parent_ids = []
        for ai_message in ai_messages:
            ai_parent_ids.append(ai_message.parent_message_id)
            for human_message in human_messages:
                if human_message.message_id == ai_parent_ids[-1]:
                    couplets.append(ChatCouplet.from_tuple((human_message, ai_message)))
                    break

        if (not (len(couplets) == len(human_messages)) or
                not (len(couplets) == len(ai_messages))):
            human_message_ids = []
            for human_message in human_messages:
                human_message_ids.append(human_message.message_id)
                if human_message_ids[-1] not in ai_parent_ids:
                    pass
                    # couplets.append(ChatCouplet.from_tuple((human_message, None)))

            for ai_message in ai_messages:
                if ai_message.parent_message_id not in ai_parent_ids:
                    pass
                    # couplets.append(ChatCouplet.from_tuple((None, ai_message)))

        return couplets

    @classmethod
    def from_dict(cls, chat_dict: dict):
        if "_id" in chat_dict:
            del chat_dict["_id"]
        messages = [DiscordMessageDocument(**message_dict) for message_dict in chat_dict["messages"]]
        couplets = [ChatCouplet.from_dict(couplet_dict) for couplet_dict in chat_dict["couplets"]]
        cls._validate_messages(message_documents=messages)
        chat_dict["messages"] = messages
        chat_dict["couplets"] = couplets

        return cls(**chat_dict)

from pathlib import Path
from typing import List, Optional, Union

import discord
from pydantic import BaseModel

from jonbot import get_logger
from jonbot.models.context_route import ContextRoute
from jonbot.models.conversation_context import ConversationContextDescription
from jonbot.models.timestamp_model import Timestamp

logger = get_logger()
from jonbot.system.path_getters import get_new_attachments_folder_path


class DiscordMessageDocument(BaseModel):
    content: str
    reference_dict: dict
    message_id: int
    author: str
    author_id: int
    server_name: str
    server_id: int
    channel_name: str
    channel_id: int
    thread_name: Optional[str]
    thread_id: Optional[int]
    is_bot: bool
    in_thread: bool
    timestamp: Timestamp
    edited_timestamp: Union[Timestamp, str]
    received_timestamp: Timestamp
    mentions: List[str]
    jump_url: str
    dump: str
    reactions: List[str]
    attachment_urls: List[str]
    attachment_local_paths: List[str]
    parent_message_id: Optional[int]
    parent_message_jump_url: Optional[str]
    context_description: str
    context_route_object: ContextRoute
    context_route_path: str
    context_route_query: dict

    @classmethod
    async def from_discord_message(cls,
                                   message: discord.Message):
        context_route = ContextRoute.from_discord_message(message)
        discord_message_document = cls(
            content=message.content,
            reference_dict=message.to_message_reference_dict(),
            message_id=message.id,
            attachment_urls=[attachment.url for attachment in message.attachments],
            attachment_local_paths=[],
            author=message.author.name,
            author_id=message.author.id,
            is_bot=message.author.bot,
            in_thread= "thread" in message.channel.type.name,
            timestamp=Timestamp.from_datetime(message.created_at),
            edited_timestamp=Timestamp.from_datetime(message.edited_at) if message.edited_at else '',
            mentions=[mention.name for mention in message.mentions],
            jump_url=message.jump_url,
            dump=str(message),
            received_timestamp=Timestamp.now(),
            reactions=[str(reaction) for reaction in message.reactions],
            parent_message_id=message.reference.message_id if message.reference else 0,
            parent_message_jump_url=message.reference.jump_url if message.reference else '',
            context_description=ConversationContextDescription.from_discord_message(message).description,
            context_route_object=context_route.dict(),
            context_route_path=context_route.as_path,
            context_route_query=context_route.as_query,
            **context_route.as_flat_dict,
        )
        await discord_message_document._add_attachments_to_message(message)
        return discord_message_document

    async def _add_attachments_to_message(self,
                                          message: discord.Message,
                                          attachment_local_path: Optional[
                                              Union[str, Path]] = get_new_attachments_folder_path(),
                                          ):
        """Save attachments from a message and add their paths to the message data.

        Args:
            message (discord.Message): Message to save attachments from.
            message_data (dict): Data of the message to add attachments to.
        """
        attachments_folder = Path(attachment_local_path)
        attachments_folder.mkdir(parents=True, exist_ok=True)
        for attachment in message.attachments:
            try:
                file_path = attachments_folder / f'{message.id}_{attachment.filename}'
                await attachment.save(file_path)
                self.attachment_local_paths.append(str(file_path))
            except Exception as e:
                logger.warning(f"Failed to save attachment: {attachment.filename}. Error: {e}")

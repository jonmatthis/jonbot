import logging
from pathlib import Path
from typing import List, Optional, Union

import discord
from pydantic import BaseModel

from jonbot.models.conversation_models import ConversationContext, ContextRoute
from jonbot.models.timestamp_model import Timestamp

logger = logging.getLogger(__name__)
from jonbot.system.path_getters import get_new_attachments_folder_path


class DiscordMessageDocument(BaseModel):
    content: str
    reference_dict: dict
    message_id: int
    attachment_urls: List[str]
    attachment_local_paths: List[str]
    author: str
    author_id: int
    channel: str
    channel_id: int
    in_thread: bool
    thread_id: Optional[int]
    server: str
    server_id: int
    timestamp: Timestamp
    edited_timestamp: Union[Timestamp, str]
    received_timestamp: Timestamp
    mentions: List[str]
    jump_url: str
    dump: str
    reactions: List[str]
    parent_message_id: Optional[int]
    parent_message_jump_url: Optional[str]
    conversational_context: ConversationContext
    context_route: ContextRoute

    @classmethod
    async def from_message(cls, message: discord.Message):
        discord_message_document = cls(
            content=message.content,
            reference_dict=message.to_message_reference_dict(),
            message_id=message.id,
            attachment_urls=[attachment.url for attachment in message.attachments],
            attachment_local_paths=[],
            author=message.author.name,
            author_id=message.author.id,
            channel=message.channel.name if message.guild else f"DM_with_{message.author.name}",
            channel_id=message.channel.id,
            server=message.guild.name if message.guild else f"DM_with_{message.author.name}",
            server_id=message.guild.id if message.guild else 0,
            timestamp=Timestamp.from_datetime(message.created_at),
            edited_timestamp=Timestamp.from_datetime(message.edited_at) if message.edited_at else '',
            mentions=[mention.name for mention in message.mentions],
            jump_url=message.jump_url,
            dump=str(message),
            received_timestamp=Timestamp.now(),
            reactions=[str(reaction) for reaction in message.reactions],
            parent_message_id=message.reference.message_id if message.reference else 0,
            parent_message_jump_url=message.reference.jump_url if message.reference else '',
            in_thread=True if message.thread else False,
            thread_id=message.thread.id if message.thread else 0,
            conversational_context=ConversationContext.from_discord_message(message),
            context_route=ContextRoute.from_discord_message(message),
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

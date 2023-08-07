import logging
from pathlib import Path
from typing import List, Optional

import discord
from pydantic import BaseModel

from jonbot.layer0_frontends.discord_bot.utilities.get_context_from_message import \
    determine_if_discord_message_is_from_a_thread, get_context_route_from_discord_message
from jonbot.layer3_data_layer.data_models.timestamp_model import Timestamp
from jonbot.layer3_data_layer.system.filenames_and_paths import get_new_attachments_folder_path

logger = logging.getLogger(__name__)


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
    edited_timestamp: Timestamp
    mentions: List[str]
    jump_url: str
    dump: str
    reactions: List[str]
    parent_message_id: Optional[int]
    parent_message_jump_url: Optional[str]
    context_route: str

    @classmethod
    async def from_message(cls, message):
        discord_message_document =  cls(
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
            timestamp=Timestamp(date_time=message.created_at),
            edited_timestamp=Timestamp(date_time=message.edited_at),
            mentions=[mention.name for mention in message.mentions],
            jump_url=message.jump_url,
            dump=str(message),
            received_timestamp=Timestamp().dict(),
            reactions=[str(reaction) for reaction in message.reactions],
            parent_message_id=message.reference.message_id if message.reference else 0,
            parent_message_jump_url=message.reference.jump_url if message.reference else '',
            in_thread=determine_if_discord_message_is_from_a_thread(message),
            thread_id=message.thread.id if message.thread else 0,
            context_route= get_context_route_from_discord_message(message)
        )
        await discord_message_document._add_attachments_to_message(message)
        return discord_message_document

    async def _add_attachments_to_message(self,
                                          message: discord.Message,
                                          ):
        """Save attachments from a message and add their paths to the message data.

        Args:
            message (discord.Message): Message to save attachments from.
            message_data (dict): Data of the message to add attachments to.
        """
        attachments_folder = Path(get_new_attachments_folder_path())
        attachments_folder.mkdir(parents=True, exist_ok=True)
        for attachment in message.attachments:
            try:
                file_path = attachments_folder / f'{message.id}_{attachment.filename}'
                await attachment.save(file_path)
                self.attachment_local_paths.append(str(file_path))
            except Exception as e:
                logger.warning(f"Failed to save attachment: {attachment.filename}. Error: {e}")

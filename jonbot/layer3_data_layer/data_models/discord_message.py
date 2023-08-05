import logging
from typing import List, Optional

from pydantic import BaseModel

from jonbot.layer3_data_layer.data_models.timestamp_model import Timestamp

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
    parent_message_id: Optional[str]
    parent_message_jump_url: Optional[str]
    context_route: str

    @classmethod
    def from_message(cls, message):
        if message.id == 1134222381758558411:
            print("wow")
        in_thread = True if message.thread else False
        try:
            if not message.guild:
                context_route = f"frontend_discord/dm_{message.channel.recipient.name}/message_{message.id}"
            else:
                if in_thread:
                    context_route = f"frontend_discord/server_{message.guild.name}/channel_{message.channel.name}/threads/{message.thread.name}/message_{message.id}"
                else:
                    context_route = f"frontend_discord/server_{message.guild.name}/channel_{message.channel.name}/messages/message_{message.id}"
        except Exception as e:
            logger.info(f"Failed to get context route for message: {message.id}")
            logger.exception(e)
            context_route = 'unknown'

        return cls(
            content=message.content,
            reference_dict=message.to_message_reference_dict(),
            message_id=message.id,
            attachment_urls=[attachment.url for attachment in message.attachments],
            attachment_local_paths=[],
            author=message.author.name,
            author_id=message.author.id,
            channel=message.channel.name,
            channel_id=message.channel.id,
            server=message.guild.name if message.guild else 'DM',
            server_id=message.guild.id if message.guild else None,
            timestamp=Timestamp(date_time=message.created_at),
            edited_timestamp=Timestamp(date_time=message.edited_at),
            mentions=[mention.name for mention in message.mentions],
            jump_url=message.jump_url,
            dump=str(message),
            received_timestamp=Timestamp().dict(),
            reactions=[str(reaction) for reaction in message.reactions],
            parent_message_id=message.reference.message_id if message.reference else None,
            parent_message_jump_url=message.reference.jump_url if message.reference else None,
            in_thread=in_thread,
            thread_id=message.thread.id if message.thread else None,
            context_route=context_route
        )

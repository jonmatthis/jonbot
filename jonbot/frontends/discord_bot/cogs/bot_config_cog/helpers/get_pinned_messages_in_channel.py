import logging
from typing import List

import discord
from discord import Forbidden

logger = logging.getLogger(__name__)


async def get_pinned_messages(channel: discord.channel) -> List[str]:
    logger.debug(f"Getting pinned messages for channel: {channel}")
    try:
        pinned_messages = await channel.pins()
        pinned_message_content = [msg.content for msg in pinned_messages if msg.content != ""]
        logger.debug(f"Channel {channel} - Pinned messages: {pinned_message_content}")
        return pinned_message_content
    except Forbidden:
        logger.debug(f"Channel {channel} - Forbidden to get pinned messages")
        return []
    except Exception as e:
        logger.error(f"Error getting pinned messages from channel: {channel}")
        logger.exception(e)
        raise

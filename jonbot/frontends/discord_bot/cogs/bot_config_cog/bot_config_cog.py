import asyncio
import logging
from copy import deepcopy
from typing import List, TYPE_CHECKING

import discord

from jonbot.backend.data_layer.models.discord_stuff.discord_message_document import DiscordMessageDocument
from jonbot.backend.data_layer.models.user_stuff.memory.context_memory_document import ContextMemoryDocument
from jonbot.frontends.discord_bot.cogs.bot_config_cog.helpers.get_pinned_messages_in_channel import get_pinned_messages
from jonbot.frontends.discord_bot.handlers.should_process_message import BOT_CONFIG_CHANNEL_NAME, \
    allowed_to_reply_to_message

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from jonbot.frontends.discord_bot.discord_bot import MyDiscordBot


class BotConfigCog(discord.Cog):
    def __init__(self, bot: "MyDiscordBot"):
        super().__init__()
        self.bot = bot

        self._bot_config_emoji = "🤖"
        self._memory_emoji = "💭"
        self._remove_memory_emoji = "❌"

    @discord.Cog.listener()
    async def on_guild_channel_pins_update(self, channel: discord.TextChannel, last_pin: discord.Message):
        logger.debug(f"Received pin update for channel: {channel}")
        self.bot.pinned_messages_by_channel_id[channel.id] = await get_pinned_messages(channel=channel)

    @discord.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        try:
            logger.debug(f"Received reaction: {payload}")
            user = self.bot.get_user(payload.user_id)
            guild = self.bot.get_guild(payload.guild_id)
            channel = self.bot.get_channel(payload.channel_id)
            # message = await channel.fetch_message(payload.message_id)
            message = self.bot.get_message(payload.message_id)

            if not allowed_to_reply_to_message(message=message,
                                               bot_id=self.bot.user.id,
                                               bot_user_name=self.bot.user.name):
                return

            emoji = str(payload.emoji)

            if guild is not None:
                if emoji == self._bot_config_emoji and BOT_CONFIG_CHANNEL_NAME in channel.name:
                    logger.debug(f"Reaction was in bot-config channel, updating config messages")
                    self.bot.config_messages_by_guild_id[payload.guild_id] = await self.get_bot_config_channel_prompts(
                        channel=channel)

            if emoji == self._memory_emoji:
                logger.debug(f"User reacted with memory emoji - adding memory message to channel ({channel}) list")
                if payload.channel_id not in self.bot.memory_messages_by_channel_id.keys():
                    self.bot.memory_messages_by_channel_id[payload.channel_id] = []

                if message not in self.bot.memory_messages_by_channel_id[payload.channel_id]:
                    message_document = await DiscordMessageDocument.from_discord_message(message=message)
                    self.bot.memory_messages_by_channel_id[payload.channel_id].append(message_document)

                if not user == self.bot.user:
                    logger.debug("Emoji was added by a user, so botto will add their own reaction")
                    await message.add_reaction(self._memory_emoji),

                logger.debug(f"Adding remove memory emoji to message: {self._remove_memory_emoji}")
                await message.add_reaction(self._remove_memory_emoji)

            if emoji == self._remove_memory_emoji and not user == self.bot.user:
                logger.debug(f"User reacted with remove memory emoji - removing memory message")
                await message.remove_reaction(self._remove_memory_emoji, self.bot.user)
                await message.remove_reaction(self._memory_emoji, self.bot.user)
                await message.remove_reaction(self._remove_memory_emoji, user)
                await message.remove_reaction(self._memory_emoji, user)

                if not payload.channel_id in self.bot.memory_messages_by_channel_id.keys():
                    self.bot.memory_messages_by_channel_id[payload.channel_id] = []
                for message in self.bot.memory_messages_by_channel_id[payload.channel_id]:
                    if message.message_id == payload.message_id:
                        for message in self.bot.memory_messages_by_channel_id[payload.channel_id]:
                            if message.message_id == payload.message_id:
                                if isinstance(message, discord.Message):
                                    message_document = await DiscordMessageDocument.from_discord_message(
                                        message=message)
                                elif isinstance(message, DiscordMessageDocument):
                                    message_document = deepcopy(message.dict())
                                else:
                                    raise ValueError(f"Message type not recognized: {message}")
                                self.bot.memory_messages_by_channel_id[payload.channel_id].remove(message_document)
                                break
                        try:
                            self.bot.memory_messages_by_channel_id[payload.channel_id].remove(message_document)
                        except ValueError:
                            logger.error(f"Message not found in memory messages: {message_document}")
                            raise
                        break
        except Exception as e:
            logger.error(f"Error handling reaction` add: {e}")
            logger.exception(e)
            raise

    async def get_memory_messages(self,
                                  channel: discord.channel,
                                  memory_emoji: str = "💭") -> List[DiscordMessageDocument]:

        memory_messages = await self.look_for_emoji_reaction_in_channel(channel=channel,
                                                                        emoji=memory_emoji)
        documents = [await DiscordMessageDocument.from_discord_message(message=message) for message in memory_messages]

        if len(documents) == 0:
            logger.trace(f"Channel: {channel} - No memory messages found")
        else:
            logger.trace(f"Channel: {channel} - Found {len(documents)} memory messages")
        return documents

    async def gather_config_messages(self,
                                     channel: discord.channel, ):
        try:
            logger.info(f"Getting config messages")

            if hasattr(channel, "guild") and channel.guild is not None:
                self.bot.config_messages_by_guild_id[channel.guild.id] = await self.get_bot_config_channel_prompts(
                    channel=channel)
            self.bot.pinned_messages_by_channel_id[channel.id] = await get_pinned_messages(channel=channel)
            self.bot.memory_messages_by_channel_id[channel.id] = await self.get_memory_messages(channel=channel)

        except Exception as e:
            logger.error(f"Error getting config messages")
            logger.exception(e)
            raise
        logger.success(f"Finished gathering config messages")

    async def get_bot_config_channel_prompts(self,
                                             channel: discord.TextChannel,
                                             bot_config_channel_name: str = BOT_CONFIG_CHANNEL_NAME,
                                             selected_emoji: str = "🤖") -> str:

        logger.debug("Getting extra prompts from bot-config channel")

        try:
            guild = channel.guild
            parent_category = channel.category

            category_channels = []
            top_level_channels = []
            for guild_channel in guild.channels:
                if guild_channel.category == parent_category:
                    category_channels.append(guild_channel)
                elif not guild_channel.category:
                    top_level_channels.append(guild_channel)

            bot_config_prompts = ""
            for prompt_type in ["top", "category"]:

                if prompt_type == "top":
                    channels = top_level_channels
                    bot_config_prompts += "# Top-Level `bot-config` prompts: \n"
                elif prompt_type == "category":
                    channels = category_channels
                    bot_config_prompts += "# Category-Level `bot-config` prompts: \n"

                for _channel in channels:
                    if bot_config_channel_name in _channel.name:
                        logger.debug(f"Found bot-config channel - {_channel}")
                        pinned_messages = await get_pinned_messages(channel=_channel)
                        pinned_messages_str = "\n".join(pinned_messages)
                        bot_config_prompts += f" ## Pins - \n {pinned_messages_str}\n\n"

                        bot_emoji_messages = await self.look_for_emoji_reaction_in_channel(channel=_channel,
                                                                                           emoji=selected_emoji)
                        emoji_prompts = [message.content for message in bot_emoji_messages]
                        emoji_prompts_str = "\n".join(emoji_prompts)
                        bot_config_prompts += f" ## {selected_emoji} tagged Messages - \n {emoji_prompts_str}\n\n"

            channel_pinned_messages = await get_pinned_messages(channel=channel)
            channel_pinned_messages_str = "\n".join(channel_pinned_messages)
            bot_config_prompts += f" # Channel-level Pinned Messages - \n {channel_pinned_messages_str}\n\n"

            return bot_config_prompts

        except Exception as e:
            logger.error("Error getting extra prompts from bot-config channel")
            logger.exception(e)
            raise

    async def update_memory_emojis(self,
                                   context_memory_document: ContextMemoryDocument,
                                   message: discord.Message):

        memory_message_ids = []
        if context_memory_document.chat_memory_message_buffer:
            if context_memory_document.chat_memory_message_buffer.message_buffer:

                for memory_message in context_memory_document.chat_memory_message_buffer.message_buffer:
                    if "message_id" in memory_message.additional_kwargs.keys():
                        memory_message_ids.append(memory_message.additional_kwargs["message_id"])

        async def update_message_inner_function(channel: discord.TextChannel, message_id: int):

            message = await channel.fetch_message(message_id)
            if "💭" not in message.reactions:
                logger.trace(f"Adding memory emoji to message id: {message.id}")
                await message.add_reaction("💭")

        current_message_ids = await self._clear_channel_memory_messages_that_arent_in_memory(memory_message_ids,
                                                                                             message)

        emoji_tasks = [
            asyncio.create_task(update_message_inner_function(channel=message.channel, message_id=memory_message_id))
            for memory_message_id in memory_message_ids if memory_message_id not in current_message_ids
        ]

        await asyncio.gather(*emoji_tasks)
        logger.success(f"Finished updating memory emojis")

    async def _clear_channel_memory_messages_that_arent_in_memory(self, memory_message_ids: List[int],
                                                                  message: discord.Message):
        try:
            current_memory_messages = await self.look_for_emoji_reaction_in_channel(channel=message.channel,
                                                                                    emoji="💭")
            current_message_ids = [message.id for message in current_memory_messages]
            for current_message_id in current_message_ids:
                if current_message_id not in memory_message_ids:
                    logger.trace(f"Removing memory emoji from message id: {current_message_id}")
                    await message.remove_reaction("💭", self.bot.user)
                    await message.remove_reaction("💭", message.author)
                    await message.remove_reaction("❌", self.bot.user)
                    await message.remove_reaction("❌", message.author)
        except Exception as e:
            logger.error(f"Error clearing memory messages that aren't in memory")
            logger.exception(e)
            raise
        return current_message_ids

    async def look_for_emoji_reaction_in_channel(self,
                                                 channel: discord.TextChannel,
                                                 emoji: str,
                                                 self_only: bool = False) -> List[discord.Message]:
        try:
            messages = []
            async for msg in channel.history(limit=100):
                # use messages with `bot` emoji reactions as prompts
                if msg.reactions:
                    for reaction in msg.reactions:
                        if str(reaction.emoji) == emoji:
                            if self_only and not reaction.me:
                                continue
                            messages.append(msg)
            return messages
        except discord.Forbidden:
            logger.debug(f"Bot does not have permission to read messages in channel: {channel.name}")
            return []
        except Exception as e:
            logger.error(f"Error looking for emoji reaction in channel: {channel.name}")
            logger.exception(e)
            raise

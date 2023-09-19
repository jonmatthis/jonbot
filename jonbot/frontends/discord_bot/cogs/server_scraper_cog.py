import asyncio
import logging
from typing import List

import discord
from discord import Forbidden
from discord.ext import commands

from jonbot.backend.data_layer.models.discord_stuff.discord_chat_document import DiscordChatDocument
from jonbot.frontends.discord_bot.operations.discord_database_operations import (
    DiscordDatabaseOperations,
)
from jonbot.system.setup_logging.get_logger import get_jonbot_logger

logger = get_jonbot_logger()

logging.getLogger("discord").setLevel(logging.INFO)


class ServerScraperCog(commands.Cog):
    """A cog for scraping server data and storing it in a MongoDB database."""

    def __init__(self, database_operations: DiscordDatabaseOperations):
        self._database_operations = database_operations

    @commands.slash_command(
        name="scrape_server",
        description="Scrape all messages from all channels and threads in the server.",
    )
    @commands.has_permissions(administrator=True)
    async def scrape_server(self, ctx: discord.ApplicationContext):
        logger.info(f"Received scrape_server command in server: {ctx.guild.name}")

        channels = await ctx.guild.fetch_channels()
        await self._scrape(channels=list(channels), ctx=ctx)

    @commands.slash_command(
        name="scrape_local",
        description="Scrape all messages from invoking thread/channel only.",
    )
    @commands.has_permissions(administrator=True)
    async def scrape_messages_from_channel(
            self,
            ctx: discord.ApplicationContext,
    ):
        logger.info(f"Received scrape_local command from channel:  {ctx.channel.name}")

        channels = [ctx.channel]
        await self._scrape(channels=channels, ctx=ctx)

    async def _scrape(self, channels: List[discord.abc.Messageable], ctx: discord.ApplicationContext):
        total_messages = 0
        channel_message_counts = []
        chat_message_counts = []
        try:
            for channel in channels:
                logger.info(f"Scraping channel:  {ctx.channel.name}")

                channel_messages = await self._get_message_list_from_channel(
                    channel=channel
                )

                chat_documents = []
                for message in channel_messages:
                    if message.thread is not None:
                        thread_messages = await self._get_message_list_from_channel(channel=message.thread)
                        chat_documents.append(await DiscordChatDocument.build(chat_id=message.thread.id,
                                                                              parent_message=message,
                                                                              messages=thread_messages))
                total_messages += len(channel_messages)

                channel_message_counts.append(f"{channel}: {len(channel_messages)} messages")

                if len(chat_documents) > 0:
                    for document in chat_documents:
                        total_messages += len(document.messages)
                        chat_message_counts.append(f"{channel}:{document.thread_name}: "
                                                   f"{len(document.messages)} messages")

                logger.info(
                    f"Upserting {len(channel_messages)} channel messages and {len(chat_documents)} chat documents to database...")

                await asyncio.gather(self._send_messages_to_database(messages_to_upsert=channel_messages),
                                     self._send_chats_to_database(chat_documents=chat_documents))
                logger.info(f"Finished upserting messages from channel: {channel} to database.")

            channel_info_string = "\n".join(channel_message_counts)
            chat_info_string = "\n".join(chat_message_counts)

            await ctx.send(
                embed=discord.Embed(
                    title=f"Scraping successful!",
                    description=f"Channel messages:\n {channel_info_string} \n\n"
                                f" Chat messages:\n {chat_info_string} \n\n "
                                f"Total messages: {total_messages}"
                )
            )
        except Exception as e:
            await ctx.send(
                embed=discord.Embed(
                    title=f"Error occurred while scraping channel: {ctx.channel.name}",
                    description=f"{e}"
                )
            )
            logger.error(f"Error occurred while scraping channel: {ctx.channel.name}: \n > {e}")
            logger.exception(e)
            raise e

    async def _send_messages_to_database(
            self, messages_to_upsert: List[discord.Message]
    ) -> bool:
        logger.info(f"Sending {len(messages_to_upsert)} messages to database...")
        return await self._database_operations.upsert_messages(
            messages=messages_to_upsert
        )

    async def _send_chats_to_database(
            self, chat_documents: List[DiscordChatDocument]
    ) -> bool:
        logger.info(f"Sending {len(chat_documents)} messages to database...")
        return await self._database_operations.upsert_chats(
            chat_documents=chat_documents
        )

    async def _get_message_list_from_channel(
            self, channel: discord.abc.Messageable
    ) -> List[discord.Message]:
        channel_messages = []
        try:
            async for message in channel.history(limit=None, oldest_first=True):
                channel_messages.append(message)
        except Forbidden:
            logger.warning(f"Missing permissions to scrape channel: {channel.name}")

        return channel_messages

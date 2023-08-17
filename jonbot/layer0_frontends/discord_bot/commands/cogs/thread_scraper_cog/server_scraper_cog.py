import asyncio
import logging
from typing import List

import discord
from discord import Forbidden
from discord.ext import commands

from jonbot import get_logger
from jonbot.layer0_frontends.discord_bot.operations.database_operations import DatabaseOperations
from jonbot.models.database_request_response_models import DatabaseUpsertRequest
from jonbot.models.discord_stuff.discord_message import DiscordMessageDocument

logger = get_logger()

logging.getLogger('discord').setLevel(logging.INFO)


class ServerScraperCog(commands.Cog):
    """A cog for scraping server data and storing it in a MongoDB database."""

    def __init__(self,
                 database_operations: DatabaseOperations):
        self._database_operations = database_operations
        self._discord_messages_to_upsert = []

    @commands.slash_command(name="scrape_server",
                            description="Scrape all messages from all channels and threads in the server.",
                            )
    @commands.has_permissions(administrator=True)
    async def scrape_server(self, ctx: discord.ApplicationContext, full_server_backup: bool = True):
        response_embed = await ctx.send(embed=discord.Embed(title="Scraping server..."))

        if full_server_backup:
            channels = await ctx.guild.fetch_channels()
        else:
            channels = [ctx.channel]

        for channel in filter(lambda ch: isinstance(ch, discord.TextChannel), channels):
            channel_messages = await self._get_message_list_from_channel(channel=channel)
            self._discord_messages_to_upsert.extend(channel_messages)

        asyncio.create_task(self._send_messages_to_database())
        response_embed.send(
            embed=discord.Embed(
                title=f"Scraping complete! Scraped and sent {len(self._discord_messages_to_upsert)} messages to the database."
            )
        )

    @commands.slash_command(name="scrape_local",
                            description="Scrape all messages from invoking thread/channel only.",
                            )
    @commands.has_permissions(administrator=True)
    async def scrape_messages_from_channel(self,
                                           channel: discord.abc.Messageable
                                           ):
        channel_messages = await self._get_message_list_from_channel(channel=channel)
        for message in channel_messages:
            await self._upsert_message_data_to_database(message=message)

    async def _get_message_list_from_channel(self,
                                                channel: discord.abc.Messageable
                                                ) -> List[discord.Message]:

        channel_messages = []
        try:
            async for message in channel.history(limit=None, oldest_first=True):
                channel_messages.append(message)
        except Forbidden:
            logger.warning(f"Missing permissions to scrape channel: {channel.name}")

        return channel_messages

    async def _send_messages_to_database(self):
        for message in self._discord_messages_to_upsert:
            await self._database_operations.log_message_in_database(message=message)

    async def _upsert_message_data_to_database(self, message: discord.Message):
        discord_message_document = await DiscordMessageDocument.from_message(message=message)
        upsert_request = DatabaseUpsertRequest(database_name=self._database_name,
                                               collection_name=self._database_collection_name,
                                               data=discord_message_document,
                                               query={
                                                   "context_route_query": discord_message_document.context_route.query()},
                                               )

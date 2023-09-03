import logging
from typing import List

import discord
from discord import Forbidden
from discord.ext import commands

from jonbot.layer0_frontends.discord_bot.operations.discord_database_operations import (
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

        messages_to_upsert = []
        response_embed_message = await ctx.send(
            embed=discord.Embed(title="Scraping server...")
        )

        channels = await ctx.guild.fetch_channels()

        for channel in filter(lambda ch: isinstance(ch, discord.TextChannel), channels):
            channel_messages = await self._get_message_list_from_channel(
                channel=channel
            )
            messages_to_upsert.extend(channel_messages)

        embed_string = f"Scraping complete! Scraped and sent {len(messages_to_upsert)} messages to the database."
        await response_embed_message.edit(embed=discord.Embed(title=embed_string))

        success = await self._database_operations.upsert_messages(
            messages=messages_to_upsert
        )

        await response_embed_message.edit(
            embed=discord.Embed(title=embed_string + "\n\nDatabase upsert complete!")
        )

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
        channel_messages = await self._get_message_list_from_channel(
            channel=ctx.channel
        )
        success = await self._send_messages_to_database(
            messages_to_upsert=channel_messages
        )
        if success:
            await ctx.send(
                embed=discord.Embed(
                    title=f"Scraped {len(channel_messages)} messages from channel: {ctx.channel.name}"
                )
            )
        else:
            await ctx.send(
                embed=discord.Embed(
                    title=f"Error occurred while scraping channel: {ctx.channel.name}"
                )
            )

    async def _send_messages_to_database(
            self, messages_to_upsert: List[discord.Message]
    ) -> bool:
        logger.info(f"Sending {len(messages_to_upsert)} messages to database...")
        return await self._database_operations.upsert_messages(
            messages=messages_to_upsert
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

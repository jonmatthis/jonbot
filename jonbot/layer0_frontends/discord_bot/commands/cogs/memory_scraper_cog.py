import asyncio
import logging

import discord
from discord import Forbidden
from discord.ext import commands

from jonbot import get_logger
from jonbot.layer1_api_interface.api_client.api_client import ApiClient
from jonbot.models.calculate_memory_request import CalculateMemoryRequest
from jonbot.models.context_route import ContextRoute

logger = get_logger()

logging.getLogger('discord').setLevel(logging.INFO)


class MemoryScraperCog(commands.Cog):
    """A cog for calculating the memory from contexts within a server."""

    def __init__(self,
                 database_name: str,
                 api_client: ApiClient, ):
        self._database_name = database_name
        self._api_client = api_client

    @discord.slash_command(name="calculate_memory_local",
                           description="Calculate the memory from messages within a channel.",
                           )
    @discord.option(name="limit_messages",
                    description="The maximum number of messages to scrape.",
                    input_type=int,
                    required=False)
    async def calculate_memory_local(self,
                                     ctx: discord.ApplicationContext,
                                     limit_messages: int = 100,
                                     ):
        logger.info(f"Received calculate_memory_local command from channel:  {ctx.channel.name}")

        response_embed = await ctx.send(embed=discord.Embed(title="Calculating memory for channel..."))

        calculate_memory_request = CalculateMemoryRequest(
            context_route=await self._get_context_route(channel=ctx.channel),
            database_name=self._database_name,
            limit_messages=limit_messages,
        )
        asyncio.create_task(self._api_client.calculate_memory(calculate_memory_request=calculate_memory_request))
        await response_embed.edit(
            embed=discord.Embed(title="Memory calculation process launched. It might take a while!"))

    async def _get_context_route(self,
                                 channel: discord.abc.Messageable
                                 ) -> ContextRoute:
        try:
            async for message in channel.history(limit=None, oldest_first=True):
                context_route = ContextRoute.from_discord_message(message=message)
                break
        except Forbidden:
            logger.warning(f"Missing permissions to scrape channel: {channel.name}")

        return context_route

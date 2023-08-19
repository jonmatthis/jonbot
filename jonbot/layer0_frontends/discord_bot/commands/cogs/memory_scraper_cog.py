import logging
from datetime import datetime

import discord
from discord.ext import commands

from jonbot import get_logger
from jonbot.layer1_api_interface.api_client.api_client import ApiClient
from jonbot.layer1_api_interface.routes import CALCULATE_MEMORY_ENDPOINT
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

    @discord.slash_command(name="memory_calc_server",
                           description="Calculate the memory from all contexts within a server.",
                           )
    @discord.option(name="limit_messages",
                    description="The maximum number of messages to scrape.",
                    input_type=int,
                    required=False)
    async def memory_calc_local(self,
                                ctx: discord.ApplicationContext,
                                limit_messages: int = None,
                                ):
        logger.info(f"Received calculate_memory_server command from channel:  {ctx.channel.name}")

        response_embed = await ctx.send(embed=discord.Embed(title="Calculating memory for channel..."))
        channels = await ctx.guild.fetch_channels()
        for channel in filter(lambda ch: isinstance(ch, discord.TextChannel), channels):
            calculate_memory_request = CalculateMemoryRequest(
                context_route=await self._get_context_route(channel=ctx.channel),
                database_name=self._database_name,
                limit_messages=limit_messages,
            )

            await response_embed.edit(
                embed=discord.Embed(title="Memory calculation process started..."))
            memory = await self._api_client.calculate_memory(calculate_memory_request=calculate_memory_request)
            await response_embed.edit(
                embed=discord.Embed(title="Memory calculation process complete!"))

    @discord.slash_command(name="memory_calc_local",
                           description="Calculate the memory from messages within a channel.",
                           )
    @discord.option(name="limit_messages",
                    description="The maximum number of messages to scrape.",
                    input_type=int,
                    required=False)
    async def memory_calc_local(self,
                                ctx: discord.ApplicationContext,
                                limit_messages: int = None,
                                ):
        logger.info(f"Received calculate_memory_local command from channel:  {ctx.channel.name}")
        reply_message = await self._initialize_reply_embed(ctx=ctx)

        response = await self._send_memory_calculation_request_from_channel(channel=ctx.channel,
                                                                            limit_messages=limit_messages)

        # attachments = discord.File(fp=response, filename=f"memory_{datetime.now().isoformat()}.json".replace(":", "_"))
        # with open('my_file.png', 'rb') as fp:
        #     await channel.send(file=discord.File(fp, 'new_filename.png'))
        await reply_message.edit(
            embed=discord.Embed(
                title=f"Memory calculation process complete for context: {response}\n "
                      f"Context summary:\n {response['summmary']}"),
        )

    async def _initialize_reply_embed(self, ctx: discord.ApplicationContext) -> discord.Message:
        return await ctx.respond(embed=discord.Embed(title=f"Calculating memory..."))

    async def _send_memory_calculation_request_from_channel(self,
                                                            channel: discord.TextChannel,
                                                            limit_messages: int = None,
                                                            ):
        request = CalculateMemoryRequest(
            context_route=ContextRoute.from_discord_channel(channel=channel),
            database_name=self._database_name,
            limit_messages=limit_messages,
        )
        response = await self._api_client.send_request_to_api(endpoint_name=CALCULATE_MEMORY_ENDPOINT,
                                                              data=request.dict())
        return response

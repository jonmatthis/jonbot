import logging
from datetime import datetime

import discord
from discord import Forbidden
from discord.ext import commands

from jonbot import get_logger
from jonbot.layer0_frontends.discord_bot.operations.database_operations import DatabaseOperations
from jonbot.layer1_api_interface.routes import DATABASE_UPSERT_ENDPOINT
from jonbot.models.conversation_models import ContextRoute
from jonbot.models.database_upsert_models import DatabaseUpsertRequest
from jonbot.models.discord_stuff.discord_message import DiscordMessageDocument

logger = get_logger()

logging.getLogger('discord').setLevel(logging.INFO)


class ServerScraperCog(commands.Cog):
    """A cog for scraping server data and storing it in a MongoDB database."""

    def __init__(self,
                 database_operations: DatabaseOperations):
        self._database_operations = database_operations
        self._message_documents_to_upsert = []

    @commands.slash_command(name="scrape_server",
                            description="Scrape all messages from all channels and threads in the server.",
                            )
    @commands.has_permissions(administrator=True)
    @discord.option(name="full_server_backup",
                    description="Whether to perform a full server scrape (if False, scrape invoking channel only).",
                    input_type=bool,
                    default=True)
    async def scrape_server(self, ctx: discord.ApplicationContext, full_server_backup: bool = True):
        """Scrape all messages from all channels and threads in the server.

        Args:
            ctx (discord.ApplicationContext): Context related to the command invocation.
        """

        response_embed = ctx.send(embed=discord.Embed(title="Scraping server..."))

        if full_server_backup:
            channels = await ctx.guild.fetch_channels()
        else:
            channels = [ctx.channel]

        for channel in filter(lambda ch: isinstance(ch, discord.TextChannel), channels):
            await self._scrape_messages_from_channel(channel)


        await self._send_messages_to_database()
        response_embed.send(embed=discord.Embed(title=f"Scraping complete! Scraped {len(self._message_documents_to_upsert)} messages."))

    async def _scrape_messages_from_channel(self,
                                            channel: discord.abc.Messageable
                                            ):

        try:
            async for message in channel.history(limit=None, oldest_first=True):
                await self._prep_message_for_database(message=message)
        except Forbidden:
            logger.warning(f"Missing permissions to scrape channel: {channel.name}")

    async def _prep_message_for_database(self, message: discord.Message):
        """Save a message to the database.

        Args:
            message (discord.Message): Message to save.
            collection_name (str): Name of the MongoDB collection to store data in.
        """
        message_document = await DiscordMessageDocument.from_message(message=message)
        await self._add_attachments_to_message(message, message_document)
        await self._message_documents_to_upsert.append(message_document)

    async def _send_messages_to_database(self):
        for message_document in self._message_documents_to_upsert:
            self._upsert_message_data_to_database(message_document=message_document)

    async def _add_attachments_to_message(self,
                                        message_document: DiscordMessageDocument):
            upsert_request = DatabaseUpsertRequest(database_name=self._database_name,
                                                   collection_name=self._database_collection_name,
                                                   data=message_document,
                                                   )

            await self._api_client.send_request_to_api(endpoint_name=DATABASE_UPSERT_ENDPOINT,
                                                       data=upsert_request.dict())


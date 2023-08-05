import logging
from datetime import datetime
from pathlib import Path

import discord
from discord import Forbidden

from jonbot.layer3_data_layer.data_models.discord_message import DiscordMessageDocument
from jonbot.layer3_data_layer.database.mongo_database import mongo_database_manager, BASE_COLLECTION_NAME
from jonbot.layer3_data_layer.system.filenames_and_paths import get_new_attachments_folder_path

logger = logging.getLogger(__name__)
logging.getLogger('discord').setLevel(logging.INFO)


class ServerScraper:
    """A cog for scraping server data and storing it in a MongoDB database."""

    async def scrape_server(self, ctx: discord.ApplicationContext):
        """Scrape all messages from all channels and threads in the server.

        Args:
            ctx (discord.ApplicationContext): Context related to the command invocation.
        """

        status_message = await self._send_scraping_start_message(ctx.author, ctx.guild.name)

        channels = await ctx.guild.fetch_channels()
        for channel in filter(lambda ch: isinstance(ch, discord.TextChannel), channels):
            await self._scrape_messages_from_channel(channel)

        await self._send_scraping_end_message(status_message, ctx.guild.name)

    async def _scrape_messages_from_channel(self,
                                            channel: discord.abc.Messageable
                                            ):
        """Scrape all messages from a particular channel or thread and save them to the database.

        Args:
            channel (discord.abc.Messageable): Channel or thread to scrape messages from.
            collection_name (str): Name of the MongoDB collection to store data in.
        """
        try:
            async for message in channel.history(limit=None, oldest_first=True):
                await self._save_message_to_database(message=message
                                                     )
        except Forbidden:
            logger.warning(f"Missing permissions to scrape channel: {channel.name}")

    async def _save_message_to_database(self, message: discord.Message):
        """Save a message to the database.

        Args:
            message (discord.Message): Message to save.
            collection_name (str): Name of the MongoDB collection to store data in.
        """
        message_document = DiscordMessageDocument.from_message(message=message)
        await self._add_attachments_to_message(message, message_document)
        await self._upsert_message_data_to_database( message_id = message.id,
                                                     message_document = message_document)

    async def _add_attachments_to_message(self,
                                          message: discord.Message,
                                          message_document: DiscordMessageDocument):
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
                message_document.attachment_local_paths.append(str(file_path))
            except Exception as e:
                logger.warning(f"Failed to save attachment: {attachment.filename}. Error: {e}")

    async def _upsert_message_data_to_database(self,
                                               message_id: int,
                                               message_document: DiscordMessageDocument,
                                               collection_name: str = BASE_COLLECTION_NAME ):

        """Update the message data in the database if it exists, else insert it.

        Args:
            collection_name (str): Name of the MongoDB collection to store data in.
            message_id (int): ID of the message.
            message_data (dict): Data of the message to upsert.
        """
        mongo_database_manager.upsert(
            collection_name=collection_name,
            query={"message_id": message_id},
            data={"$set": message_document.dict()},
        )

    @staticmethod
    async def _send_scraping_start_message(author: discord.User, server_name: str):
        """Send a message indicating the start of server scraping.

        Args:
            author (discord.User): The user to send the message to.
            server_name (str): The name of the server being scraped.

        Returns:
            discord.Message: The sent message.
        """
        return await author.send(f"Scraping server: {server_name} on {datetime.now().isoformat()}\n___________\n")

    @staticmethod
    async def _send_scraping_end_message(status_message: discord.Message, server_name: str):
        """Edit the status message to indicate the end of server scraping.

        Args:
            status_message (discord.Message): The status message to edit.
            server_name (str): The name of the server being scraped.
        """
        await status_message.edit(content=f"Finished scraping server: {server_name}")

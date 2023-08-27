import discord

from jonbot import get_logger
from jonbot.models.timestamp_model import Timestamp

logger = get_logger()


class ThreadCog(discord.Cog):
    @discord.slash_command(name="thread", description="Open a thread at this location")
    async def create_thread(self, ctx: discord.ApplicationContext):
        logger.debug(f"Creating thread in channel {ctx.channel.name}")
        chat_title = (
            f"{ctx.author.name}'s thread {Timestamp.now().human_friendly_local}"
        )
        message = await ctx.send(f"Creating thread {chat_title}...")
        thread = await message.create_thread(name=chat_title)
        logger.success(f"Created thread {thread.name} in channel {ctx.channel.name}")

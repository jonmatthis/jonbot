import asyncio
import tempfile
from datetime import datetime
from typing import TYPE_CHECKING

import discord

from jonbot.backend.data_layer.models.context_route import ContextRoute
from jonbot.frontends.discord_bot.handlers.should_process_message import (
    NEW_CHAT_MESSAGE_PREFIX_TEXT,
)
from jonbot.system.setup_logging.get_logger import get_jonbot_logger

logger = get_jonbot_logger()

if TYPE_CHECKING:
    from jonbot.frontends.discord_bot.discord_bot import MyDiscordBot


class DMCog(discord.Cog):

    def __init__(self, bot: "MyDiscordBot"):
        super().__init__()
        self.bot = bot

    @discord.slash_command(name="send_dms",
                           description="Open new thread if in a thread or channel, new post if in a forum) ")
    @discord.option(
        name="test_cog",
        description="testing the cog",
        input_type=bool,
        required=False,
    )

    async def send_dms(
        self,
        ctx: discord.ApplicationContext,
        test: bool = True) -> discord.Message:

        # Specify the user_id of the 'test' user.
        allowed_user = 362711467104927744

        # Check if the user who triggered the cog is the 'test' user.
        if ctx.author.id != allowed_user:
            return await ctx.send("Sorry, you do not have permission to use this command.")

        initial_message = "Hello there! How are you doing today?"
        users_to_message = [362711467104927744] if test else [member.id for member in ctx.guild.members]

        message_queue = asyncio.Queue()

        for user_id in users_to_message:
            await message_queue.put(user_id)

        while not message_queue.empty():
            user_id = await message_queue.get()

            user = self.bot.get_user(user_id)
            if user is not None:
                try:
                    await user.send(initial_message)
                    logger.info(f'Successfully sent message to: {user.id}')
                except discord.errors.Forbidden:
                    logger.warning(f'Unable to send message to: {user.id}, likely due to privacy settings.')
                except Exception as e:
                    logger.error(f'Unexpected error occurred while sending message to: {user.id}, Error: {e}')
                finally:
                    message_queue.task_done()

        return discord.Message
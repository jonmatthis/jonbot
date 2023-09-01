from datetime import datetime

import discord

from jonbot import get_jonbot_logger
from jonbot.layer0_frontends.discord_bot.handlers.should_process_message import (
    NEW_THREAD_MESSAGE_PREFIX_TEXT,
)
from jonbot.models.context_route import ContextRoute
from jonbot.models.timestamp_model import Timestamp

logger = get_jonbot_logger()


class ThreadCog(discord.Cog):
    @discord.slash_command(name="thread", description="Open a thread at this location")
    @discord.option(
        name="initial_message",
        description="The initial message to send to the bot",
        input_type=str,
        required=False,
    )
    async def create_thread(
        self,
        ctx: discord.ApplicationContext,
        initial_message: str = None,
    ):
        logger.info(
            f"Received thread request from {ctx.user.name} with initial message: {initial_message}"
        )
        reply_message = await self._send_title_card_as_reply_message(ctx)

        await self._spawn_thread(
            parent_message=reply_message,
            user_name=str(ctx.user),
            initial_text_input=initial_message,
        )

    async def _spawn_thread(
        self,
        parent_message: discord.Message,
        user_name: str,
        initial_text_input: str = None,
    ):
        logger.debug(f"Spawning thread for {user_name}")
        thread_title = self._create_chat_title_string(user_name=user_name)

        thread = await parent_message.create_thread(name=thread_title)

        if initial_text_input is None:
            starting_text = f"User: {user_name} has requested to chat"
        else:
            starting_text = (
                f"User: {user_name} has requested to chat with the initial message:\n"
                f" > {initial_text_input}"
            )

        initial_message_embed = self._initial_message_embed(
            message=parent_message,
            initial_message=initial_text_input,
        )
        logger.debug(
            f"Sending initial message embed to thread: {thread.id} title: {thread_title}"
        )
        await thread.send(embed=initial_message_embed)

        initial_message = f"{NEW_THREAD_MESSAGE_PREFIX_TEXT} \n" f"{starting_text}"
        logger.debug(f"Sending initial message to thread: {initial_message}")
        await thread.send(initial_message)

    def _create_chat_title_string(self, user_name: str) -> str:
        return f"{user_name}'s thread {Timestamp.now().human_friendly_local}"

    async def _send_title_card_as_reply_message(self, ctx):
        logger.debug(f"Sending title card as reply message to {ctx.user.name}")
        chat_title = self._create_chat_title_string(user_name=str(ctx.user))
        title_card_embed = await self._make_thread_title_embed(
            str(ctx.user), chat_title
        )
        reply_message = await ctx.send(embed=title_card_embed)
        return reply_message

    async def _make_thread_title_embed(self, user_name: str, chat_title: str):
        return discord.Embed(
            title=chat_title,
            description=f"A conversation between {user_name} and the bot, started on {datetime.now()}",
            color=0x25D790,
        )

    def _initial_message_embed(self, message, initial_message):
        thread_intro = f"""                      
                   Source code: 
                   https://github.com/jonmatthis/jonbot
                   
                   This bot's prompt: 
                   https://github.com/jonmatthis/jonbot/blob/main/jonbot/layer2_processing/ai/chatbot_llm_chain/components/prompt/prompt_strings.py
                    
                    Context route: {ContextRoute.from_discord_message(message).friendly_path}
                    
                   ------------------
                   Beginning chat with initial message: 

                   > {initial_message}

                   """
        return discord.Embed(
            description=thread_intro,
            color=0x25D790,
        )

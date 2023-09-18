from datetime import datetime

import discord

from jonbot.backend.data_layer.models.context_route import ContextRoute
from jonbot.frontends.discord_bot.handlers.should_process_message import (
    NEW_THREAD_MESSAGE_PREFIX_TEXT,
)
from jonbot.system.setup_logging.get_logger import get_jonbot_logger

MAX_FORUM_TITLE_LENGTH = 100
logger = get_jonbot_logger()


class ChatCog(discord.Cog):
    @discord.slash_command(name="chat",
                           description="Open new thread if in a thread or channel, new post if in a forum) ")
    @discord.option(
        name="initial_message",
        description="The initial message to send to the bot",
        input_type=str,
        required=False,
    )
    async def create_chat(
            self,
            ctx: discord.ApplicationContext,
            initial_message_text: str = None,
    ):
        logger.info(
            f"Received chat request from {ctx.user.name} with initial message: {initial_message_text}"
        )
        chat_title = self._create_chat_title_string(user_name=str(ctx.user))
        if initial_message_text is None:
            initial_message_text = f"{NEW_THREAD_MESSAGE_PREFIX_TEXT} \n" f"User: {ctx.user.name} has requested to chat"

        parent_message_embed = await self._create_parent_message_embed(ctx=ctx, chat_title=chat_title)
        in_existing_chat = False

        if hasattr(ctx.channel, "parent") and "forum" in str(ctx.channel.parent.type):
            logger.debug(
                f"Create chat called from forum, creating thread in parent channel: {ctx.channel.parent.name}")
            reply_post = await ctx.channel.parent.create_thread(name=chat_title, content=initial_message_text)
            reply_message = await reply_post.send(embed=parent_message_embed)
            in_existing_chat = True
        else:
            if "thread" in str(ctx.channel.type):
                logger.debug(
                    f"Create chat called from thread, creating thread in parent channel: {ctx.channel.parent.name}")
                reply_message = await ctx.channel.parent.send(embed=parent_message_embed)
                in_existing_chat = True
            else:
                logger.debug(f"Creating chat in {ctx.channel.name}")
                reply_message = await ctx.channel.send(embed=parent_message_embed)

            initial_message = await self._spawn_thread(
                parent_message=reply_message,
                user_name=str(ctx.user),
                initial_text_input=initial_message_text,
            )

        if in_existing_chat:
            await ctx.send(
                f"Created chat in parent channel: {ctx.channel.parent.name}:\n\n {initial_message.jump_url}")

    async def _spawn_thread(
            self,
            parent_message: discord.Message,
            user_name: str,
            initial_text_input: str = None,
    ) -> discord.Message:
        logger.debug(f"Spawning chat for {user_name}")
        thread_title = self._create_chat_title_string(user_name=user_name,
                                                      initial_text_input=initial_text_input)

        thread = await parent_message.create_thread(name=thread_title)

        starting_message = await thread.send("Creating thread...")

        if initial_text_input is None:
            starting_text = f"User: {user_name} has requested to chat"
        else:
            starting_text = (
                f"User: {user_name} has requested to chat with the initial message:\n"
                f" > {initial_text_input}"
            )

        initial_message_embed = self._initial_message_embed(starting_message=starting_message)
        logger.debug(
            f"Sending initial message embed to thread: {thread.id} title: {thread_title}"
        )
        await starting_message.edit(content=f"Thread title: {thread_title}",
                                    embed=initial_message_embed)

        initial_message_text = f"{NEW_THREAD_MESSAGE_PREFIX_TEXT} \n" f"{starting_text}"
        logger.debug(f"Sending initial message to thread: {initial_message_text}")

        initial_message = await thread.send(initial_message_text)
        return initial_message

    def _create_chat_title_string(self, user_name: str,
                                  initial_text_input: str = None) -> str:

        if initial_text_input is not None:
            return initial_text_input[:MAX_FORUM_TITLE_LENGTH]

        return f"{user_name}'s chat"

    async def _create_parent_message_embed(self,
                                           ctx: discord.ApplicationContext,
                                           chat_title: str) -> discord.Embed:
        logger.debug(f"Sending title card as reply message to {ctx.user.name}")
        return await self._make_thread_title_embed(
            str(ctx.user), chat_title
        )

    async def _make_thread_title_embed(self, user_name: str, chat_title: str):
        return discord.Embed(
            title=chat_title,
            description=f"A conversation between {user_name} and the bot, started on {datetime.now()}",
            color=0x25D790,
        )

    def _initial_message_embed(self,
                               starting_message: discord.Message
                               ) -> discord.Embed:
        thread_intro = f"""                      
                   Source code: 
                   https://github.com/jonmatthis/jonbot
                   
                   This bot's prompt: 
                   https://github.com/jonmatthis/jonbot/blob/main/jonbot/layer2_processing/ai/chatbot_llm_chain/components/prompt/prompt_strings.py
                    
                    Context route: {ContextRoute.from_discord_message(starting_message).friendly_path}
                   """
        return discord.Embed(
            description=thread_intro,
            color=0x25D790,
        )

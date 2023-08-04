import logging
import os
from datetime import datetime

import discord

from chatbot.ai.assistants.course_assistant.course_assistant import CourseAssistant
from chatbot.ai.assistants.course_assistant.prompts.general_course_assistant_prompt import \
    GENERAL_COURSE_ASSISTANT_SYSTEM_TEMPLATE
from chatbot.ai.assistants.course_assistant.prompts.project_manager_prompt import PROJECT_MANAGER_TASK_PROMPT
from chatbot.discord_bot.cogs.chat_cog.chat_model import Chat
from chatbot.discord_bot.cogs.video_chatter_cog import VIDEO_CHAT_CHANNEL_ID
from chatbot.mongo_database.mongo_database_manager import MongoDatabaseManager
from chatbot.system.environment_variables import get_admin_users

TIME_PASSED_MESSAGE = """
> Some time passed and your memory of this conversation reset needed to be reloaded from the thread, but we're good now!
> 
> Provide the human with a brief summary of what you remember about them and this conversation so far.
"""

logger = logging.getLogger(__name__)


class ChatCog(discord.Cog):
    def __init__(self,
                 bot: discord.Bot,
                 mongo_database_manager: MongoDatabaseManager):
        self._discord_bot = bot
        self._mongo_database = mongo_database_manager
        self._active_threads = {}
        self._allowed_channels = os.getenv("ALLOWED_CHANNELS").split(",")
        self._allowed_channels = [int(channel) for channel in self._allowed_channels]
        self._course_assistant_llm_chains = {}

    @discord.slash_command(name="chat", description="Chat with the bot")
    @discord.option(name="use_project_manager_prompt?",
                    description="Whether or not this is a project manager prompt",
                    input_type=bool,
                    required=False)
    @discord.option(name="initial_message",
                    description="The initial message to send to the bot",
                    input_type=str,

                    required=False)
    async def chat(self,
                   ctx: discord.ApplicationContext,
                   use_project_manager_prompt: bool = False,
                   initial_text_input: str = None):

        if not ctx.channel.id in self._allowed_channels:
            logger.info(f"Channel {ctx.channel.id} is not allowed to start a chat")
            return

        if ctx.channel.id == VIDEO_CHAT_CHANNEL_ID:
            return

        student_user_name = str(ctx.user)
        if use_project_manager_prompt:
            chat_title = self._create_chat_title_string(user_name=student_user_name, task_type="Project")
        else:
            chat_title = self._create_chat_title_string(user_name=student_user_name)

        logger.info(f"Starting chat {chat_title}")

        title_card_embed = await self._make_title_card_embed(str(ctx.user), chat_title)
        message = await ctx.send(embed=title_card_embed)

        await self._spawn_thread(message=message,
                                 student_user_name=student_user_name,
                                 initial_text_input=initial_text_input,
                                 use_project_manager_prompt=use_project_manager_prompt)

    @discord.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        try:
            # Make sure we won't be replying to ourselves.
            if payload.user_id == self._discord_bot.user.id:
                return

            # Make sure we're only responding to the correct emoji
            if not payload.emoji.name == '🧠':
                return

            # Make sure we're only responding to the admin users
            if not payload.user_id in get_admin_users():
                logger.info(f"User {payload.user_id} is not an admin user")
                return

            # Get the channel and message using the payload
            channel = self._discord_bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            student_user_name = str(message.author)
            await self._spawn_thread(message=message,
                                     initial_text_input=message.content,
                                     student_user_name=student_user_name)


        except Exception as e:
            print(f'Error: {e}')

    @discord.Cog.listener()
    async def on_message(self, message: discord.Message):
        logger.info(f"Received message: {message.content}")

        # Make sure we won't be replying to ourselves.
        if message.author.id == self._discord_bot.user.id:
            return


        if message.channel.parent_id == VIDEO_CHAT_CHANNEL_ID:
            return


        # Only respond to messages in threads
        if not message.channel.__class__ == discord.Thread:
            return
        thread = message.channel
        # Only respond to messages in threads owned by the bot
        if not thread.owner_id == self._discord_bot.user.id:
            return

        # ignore if first character is ~
        if message.content[0] == "~":
            return
        try:
            chat = self._active_threads[thread.id]
        except KeyError:
            chat = await self._create_chat(thread=thread,
                                           student_discord_username=str(message.author)
                                           )

        logger.info(f"Sending message to the agent: {message.content}")

        await self._async_send_message_to_bot(chat=chat, input_text=message.content)

    async def _async_send_message_to_bot(self, chat: Chat, input_text: str):
        response_message = await chat.thread.send("`Awaiting bot response...`")
        try:

            async with response_message.channel.typing():
                bot_response = await chat.assistant.async_process_input(input_text=input_text)

            await response_message.edit(content=bot_response)

        except Exception as e:
            logger.error(e)
            await response_message.edit(content=f"Whoops! Something went wrong! 😅 \nHere is the error:\n ```\n{e}\n```")

    def _create_chat_title_string(self, user_name: str, task_type: str = None) -> str:
        if task_type is None:
            return f"{user_name}'s chat with {self._discord_bot.user.name}"

        return f"{user_name}'s - {task_type} Chat"

    async def _spawn_thread(self,
                            message: discord.Message,
                            student_user_name: str,
                            initial_text_input: str = None,
                            use_project_manager_prompt: bool = False
                            ):

        chat_title = self._create_chat_title_string(user_name=student_user_name)
        thread = await message.create_thread(name=chat_title)

        chat = await self._create_chat(thread=thread,
                                       student_discord_username=student_user_name,
                                       use_project_manager_prompt=use_project_manager_prompt)

        if initial_text_input is None:
            initial_text_input = f"A human has requested a chat!"

        if thread.message_count == 0:
            await chat.thread.send(
                embed=self._initial_message_embed(message=message, initial_message=initial_text_input))

        await self._async_send_message_to_bot(chat=chat,
                                              input_text=initial_text_input)

    async def _create_chat(self,
                           thread: discord.Thread,
                           student_discord_username: str,
                           use_project_manager_prompt: bool = False) -> Chat:

        if thread.id in self._active_threads:
            logger.warning(f"Thread {thread.id} already exists! Returning existing chat")
            return self._active_threads[thread.id]

        assistant = await self._get_assistant(thread, student_discord_username=student_discord_username,
                                              use_project_manager_prompt=use_project_manager_prompt)

        chat = Chat(
            title=self._create_chat_title_string(user_name=student_discord_username),
            thread=thread,
            assistant=assistant
        )

        self._active_threads[thread.id] = chat
        return chat

    async def _get_assistant(self,
                             thread: discord.Thread,
                             student_discord_username: str,
                             use_project_manager_prompt: bool = False) -> CourseAssistant:

        student_summary = self._mongo_database.get_student_summary(discord_username=student_discord_username)

        if use_project_manager_prompt:
            prompt = PROJECT_MANAGER_TASK_PROMPT
        else:
            prompt = GENERAL_COURSE_ASSISTANT_SYSTEM_TEMPLATE

        assistant = CourseAssistant(prompt=prompt,
                                    student_summary=student_summary,
                                    )
        if thread.message_count > 0:
            message = await thread.send(
                f"> Reloading bot memory from thread history...")
            await assistant.load_memory_from_thread(thread=thread,
                                                    bot_name=str(self._discord_bot.user))

            await message.edit(content=f"> Bot memory loaded from thread history.")
        return assistant

    async def _make_title_card_embed(self, user_name: str, chat_title: str):
        return discord.Embed(
            title=chat_title,
            description=f"A conversation between {user_name} and the bot, started on {datetime.now()}",
            color=0x25d790,
        )

    def _initial_message_embed(self, message, initial_message):
        thread_intro = f"""
                   Remember! The bot...                   
                   ...ignores messages starting with ~                                
                   ...makes things up some times                    
                   ...cannot search the internet 
                   ...is doing its best 🤖❤️  
                   
                   Source code: 
                   https://github.com/jonmatthis/chatbot
                   This bot's prompt: 
                   https://github.com/jonmatthis/chatbot/blob/main/chatbot/assistants/course_assistant/course_assistant_prompt.py
                   
                   ------------------
                   ------------------
                   Beginning chat with initial message: 
                   
                   > {initial_message}
                    
                   """
        return discord.Embed(
            description=thread_intro,
            color=0x25d790,
        )

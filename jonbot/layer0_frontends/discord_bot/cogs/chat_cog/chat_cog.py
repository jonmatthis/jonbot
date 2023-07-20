import logging
from datetime import datetime

import asyncio

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
        self._course_assistant_llm_chains = {}
        self.response_message = None
        self.stream_message_callback = StreamMessageHandler(asyncio.get_event_loop())
    @discord.slash_command(name="chat", description="Chat with the bot")
    @discord.option(name="initial_message",
                    description="The initial message to send to the bot",
                    input_type=str,
                    required=False)
    async def chat(self,
                   ctx: discord.ApplicationContext,
                   initial_text_input: str = None):

        student_user_name = str(ctx.user)
        chat_title = self._create_chat_title_string(user_name=student_user_name)

        logger.info(f"Starting chat {chat_title}")

        title_card_embed = await self._make_title_card_embed(str(ctx.user), chat_title)
        message = await ctx.send(embed=title_card_embed)

        await self._spawn_thread(message=message,
                                 student_user_name=student_user_name,
                                 initial_text_input=initial_text_input)


    @discord.Cog.listener()
    async def on_message(self, message: discord.Message):
        logger.info(f"Received message: {message.content}")

        # Make sure we won't be replying to ourselves.
        if message.author.id == self._discord_bot.user.id:
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
                                           user_id=str(message.author)
                                           )

        logger.info(f"Sending message to the agent: {message.content}")

        await self._async_send_message_to_bot(chat=chat, input_text=message.content)


    async def _async_send_message_to_bot(self, chat: ThreadChat, input_text: str):
        self.response_message = await chat.thread.send("Awaiting bot response")
        self.stream_message_callback.current_message = self.response_message
        self.stream_message_callback.start()

        try:
            async with self.response_message.channel.typing():
                bot_response = await chat.assistant.async_process_input(input_text=input_text)

            await self.response_message.edit(content=bot_response)

        except Exception as e:
            logger.error(e)
            await self.response_message.edit(content=f"Whoops! Something went wrong! 😅 \nHere is the error:\n ```\n{e}\n```")

        self.response_message = None
        self.stream_message_callback.stop()
        self.stream_message_callback.current_message = None


    def _create_chat_title_string(self, user_name: str, task_type: str = None) -> str:
        if task_type is None:
            return f"{user_name}'s chat with {self._discord_bot.user.name}"

        return f"{user_name}'s - {task_type} Chat"

    async def _spawn_thread(self,
                            message: discord.Message,
                            student_user_name: str,
                            initial_text_input: str = None,
                            ):

        chat_title = self._create_chat_title_string(user_name=student_user_name)
        thread = await message.create_thread(name=chat_title)

        chat = await self._create_chat(thread=thread,
                                       user_id=student_user_name)

        if initial_text_input is None:
            initial_text_input = f"A human has requested a chat!"

        if thread.message_count == 0:
            await chat.thread.send(
                embed=self._initial_message_embed(message=message, initial_message=initial_text_input))

        await self._async_send_message_to_bot(chat=chat,
                                              input_text=initial_text_input)

    async def _create_chat(self,
                           thread: discord.Thread,
                           user_id: str) -> ThreadChat:

        if thread.id in self._active_threads:
            logger.warning(f"Thread {thread.id} already exists! Returning existing chat")
            return self._active_threads[thread.id]

        assistant = await self._get_assistant(thread)
        assistant.add_callback(self.stream_message_callback)

        chat = ThreadChat(
            title=self._create_chat_title_string(user_name=user_id),
            thread=thread,
            assistant=assistant
        )

        self._active_threads[thread.id] = chat
        return chat

    async def _get_assistant(self,
                             thread: discord.Thread) -> Chatbot:

        assistant = Chatbot()
        await assistant.create_chatbot()
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

                   ------------------
                   ------------------
                   Beginning chat with initial message: 
                   
                   > {initial_message}
                    
                   """
        return discord.Embed(
            description=thread_intro,
            color=0x25d790,
        )

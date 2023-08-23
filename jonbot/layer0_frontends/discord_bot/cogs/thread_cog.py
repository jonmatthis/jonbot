import discord

from jonbot.models.timestamp_model import Timestamp


class ThreadCog(discord.Cog):
    @discord.slash_command(name="thread", description="Open a thread at this location")
    async def create_thread(self, ctx: discord.ApplicationContext):

        chat_title = f"{ctx.author.name}'s thread {Timestamp.now().human_friendly_local}"
        reply = await ctx.respond(chat_title)
        thread = await reply.create_thread(name=chat_title)
        await thread.send(f"Thread {chat_title} created!")
[[]]
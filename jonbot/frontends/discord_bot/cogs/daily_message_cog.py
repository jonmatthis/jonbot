from typing import List

import discord
from discord.ext import commands, tasks


class DailyMessageCog(commands.Cog):
    def __init__(self, bot, user_ids: List[int]):
        self.bot = bot
        self.user_ids = user_ids

    def cog_unload(self):
        self.send_daily_message.cancel()

    @tasks.loop(minutes=1.0)
    async def send_daily_message(self):
        for user_id in self.user_ids:
            user = await self.bot.fetch_user(user_id)
            await user.send("This is a daily message")

    @discord.slash_command(name="start", description="Starts sending a daily message")
    async def start(self, ctx):
        await ctx.respond("Starting daily message")
        self.send_daily_message.start()

    @discord.slash_command(name="stop", description="Stops sending a daily message")
    async def stop(self, ctx):
        await ctx.respond("Stopping daily message")
        self.send_daily_message.cancel()

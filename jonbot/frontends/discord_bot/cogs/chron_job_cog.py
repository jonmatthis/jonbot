from typing import List

from discord.ext import commands, tasks


class DailyMessageCog(commands.Cog):
    def __init__(self, bot, user_ids: List[int]):
        self.bot = bot
        self.send_daily_message.start()
        self.user_ids = user_ids

    def cog_unload(self):
        self.send_daily_message.cancel()

    @tasks.loop(minutes=1.0)
    async def send_daily_message(self):
        for user_id in self.user_ids:
            user = await self.bot.fetch_user(user_id)
            await user.send("This is a daily message")

    @commands.command()
    async def start(self, ctx):
        self.send_daily_message.start()

    @commands.command()
    async def stop(self, ctx):
        self.send_daily_message.cancel()

import logging

import discord


logger = logging.getLogger(__name__)


class DiscordBot(discord.Bot):
    def __init__(self,
                 mongo_database: MongoDatabaseManager):
        super().__init__(intents=discord.Intents.all())
        self.mongo_database = mongo_database

    @discord.Cog.listener()
    async def on_ready(self):
        logger.info("Bot is ready!")
        print(f"{self.user} is ready and online!")

    @discord.Cog.listener()
    async def on_message(self, message):
        logger.info(f"Received message: {message.content}")
        print(f"Received message: {message.content}")
        if message.guild is None:
            server_name = 'DM-with-' + str(message.author)
            channel_name = 'DM-with-' + str(message.author)
            collection_name = "dm_messages"
        else:
            server_name = message.guild.name
            channel_name = message.channel.name
            collection_name = f"server_{message.guild.name}_messages"

        await self.mongo_database.upsert(
            collection=collection_name,
            query={"server_name": server_name},
            data={"$push": {"messages": {
                'author': str(message.author),
                'author_id': message.author.id,
                'user_id': message.author.id,
                'content': message.content,
                'timestamp': message.created_at.isoformat(),
                'guild': server_name,
                'channel': channel_name,
                'jump_url': message.jump_url,
                'thread': message.thread if message.thread else 'None',
                'dump': str(message)
            }}}
        )

    @discord.slash_command(name="hello", description="Say hello to the bot")
    async def hello(self, ctx):
        logger.info(f"Received hello command: {ctx}")
        await ctx.respond("Hey!")

    def run(self, token: str):
        self.run(token)

import aiohttp
import discord


class DiscordBot(discord.Client):
    """
    Simple Discord bot for relaying user messages to an API endpoint and then back to the user.
    """

    def __init__(self, api_url: str, *args, **kwargs):
        """
        Initialize the Discord bot with the API endpoint URL.

        Parameters
        ----------
        api_url : str
            The API endpoint URL to which the bot should send user messages.
        """
        super().__init__(*args, **kwargs)
        self.api_url = api_url

    async def on_ready(self) -> None:
        """
        Print a message when the bot has connected to Discord.
        """
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

    async def on_message(self, message: discord.Message) -> None:
        """
        Handle a new message event from Discord.

        Parameters
        ----------
        message : discord.Message
            The message event data from Discord.
        """
        if message.author == self.user:
            return

        async with aiohttp.ClientSession() as session:
            payload = {"chat_input": {"message": message.content}}
            async with session.post(self.api_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    await message.channel.send(data["response"])
                else:
                    await message.channel.send("Sorry, I'm currently unable to process your request.")


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()
    bot = DiscordBot(api_url="http://localhost:8000/chat",
                     intents=discord.Intents.all())
    bot.run(os.getenv("DISCORD_TOKEN"))

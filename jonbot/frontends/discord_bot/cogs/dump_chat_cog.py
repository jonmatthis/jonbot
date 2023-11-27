from typing import TYPE_CHECKING

import aiohttp
import discord

if TYPE_CHECKING:
    from jonbot.frontends.discord_bot.discord_bot import MyDiscordBot


class DumpChatCog(discord.Cog):

    def __init__(self, bot: "MyDiscordBot"):
        super().__init__()
        self.bot = bot

    async def get_attachment_content(self, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                text = await resp.text()
        return text

    @discord.slash_command(name="dump_chat",
                           description="Saves this chat (thread) as a markdown file and returns it as an attachment")
    async def dump_chat(self,
                        ctx: discord.ApplicationContext,
                        ) -> None:
        chat_history = []
        async for message in ctx.channel.history(oldest_first=True):
            author_info = f"{message.author} (id: {message.author.id})"
            if message.author.bot:
                author_info += " [Bot]"
            chat_history.append(f"## {author_info}\n\n{message.content}\n\n")

            for attachment in message.attachments:
                if attachment.content_type and 'text' in attachment.content_type:
                    content = await self.get_attachment_content(attachment.url)
                    chat_history.append(
                        f"\n\n---\n\n**Attachment:** [Link]({attachment.url})\n\n```\n\n{content}\n\n```\n\n---\n\n")

        filename_prefix = "channel" if isinstance(ctx.channel, discord.TextChannel) else "thread"
        filename = f"{filename_prefix}_{ctx.channel.id}.md"
        filename = filename.replace(":", "_").replace(" ", "").replace("/", "_").replace("\\", "_")
        with open(filename, 'w', encoding="utf-8") as file:
            file.write('\n'.join(chat_history))

        await ctx.send(file=discord.File(filename))

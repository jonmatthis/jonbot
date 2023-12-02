import os
from io import BytesIO

import discord
import requests
from PIL import Image
from discord import Forbidden
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from openai import OpenAI

from jonbot import logger


class ImageGenerator:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI()

    def generate_image(self, prompt="an otherworldly entity, madness to behold (but kuwaii af)",
                       size="1024x1024", quality="standard", n=1):
        response = self.client.images.generate(model="dall-e-3", prompt=prompt, size=size, quality=quality, n=n)
        return response.data[0].url

    def download_and_save_image(self, url):
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        img.save("pic.png")

    def display_image(self):
        if os.name == 'nt':
            os.system("start pic.png")
        else:
            os.system("xdg-open pic.png")


class ImageGeneratorCog(discord.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.image_generator = ImageGenerator()

    @discord.slash_command(name="image", help="Generates an image based on the given query string")
    async def generate_image(self, ctx, query: str):
        # Use the ImageGenerator class to generate, download, and save the image
        image_url = self.image_generator.generate_image(query)
        self.image_generator.download_and_save_image(image_url)

        # Return a message with the query and the image as an attachment
        await ctx.send(f"Image for `{query}`", file=discord.File('pic.png'))

    @discord.slash_command(name="dream_this_chat",
                           help="summarize this chat and generate an image based on the summary")
    @discord.option(
        name="summary_prompt",
        description="the prompt that will beused to convert this chat into an image generation prompt",
        input_type=str,
        required=False,
        default="Use this text as a starting point to  generate a beautiful, complex, and detailed prompt for an image generation AI"
    )
    async def dream_this_chat(self, ctx,
                              summary_prompt: str = "Use this text as a starting point to  generate a beautiful, complex, and detailed prompt for an image generation AI"):
        chat_string = await self._get_chat_string(ctx.channel)

        prompt_template = (summary_prompt +
                           "\n\n++++++++++"
                           "\n\n {text} "
                           "\n\n++++++++++"
                           "\n\n Remember, your job is to " + summary_prompt +
                           "\n\n Do not include any text in your response other than the summary"
                           )

        llm = ChatOpenAI(temperature=.7, model_name="gpt-3.5-turbo-16k")
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | llm
        response = await chain.ainvoke(input={"text": chat_string})
        image_url = self.image_generator.generate_image(response.content)
        self.image_generator.download_and_save_image(image_url)

        # Return a message with the query and the image as an attachment
        await ctx.send(f"Image for: \n\n ```\n\n {response.content}\n\n```\n\n", file=discord.File('pic.png'))

    async def _get_chat_string(self,
                               channel: discord.abc.Messageable,
                               list_length: int = 100
                               ) -> str:
        channel_messages = []
        try:
            logger.info(f"Scraping channel: {channel}")
            async for message in channel.history(limit=list_length, oldest_first=True):
                channel_messages.append(message)
            logger.info(f"Scraped {len(channel_messages)} messages from channel: {channel}")

        except Forbidden:
            logger.warning(f"Missing permissions to scrape channel: {channel}")

        chat_string = ""
        for message in channel_messages:
            chat_string += message.content + "\n\n"
        return chat_string


if __name__ == '__main__':
    image_generator = ImageGenerator()
    image_url = image_generator.generate_image()
    image_generator.download_and_save_image(image_url)
    image_generator.display_image()

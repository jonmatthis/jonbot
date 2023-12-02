import os
from io import BytesIO

import discord
import requests
from PIL import Image
from discord.ext import commands
from dotenv import load_dotenv
from openai import OpenAI


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


class ImageGeneratorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.image_generator = ImageGenerator()

    @commands.command(name="image", help="Generates an image based on the given query string")
    async def generate_image(self, ctx, *, query: str):
        # Use the ImageGenerator class to generate, download, and save the image
        image_url = self.image_generator.generate_image(query)
        self.image_generator.download_and_save_image(image_url)

        # Return a message with the query and the image as an attachment
        await ctx.send(f"Image for `{query}`", file=discord.File('pic.png'))


if __name__ == '__main__':
    image_generator = ImageGenerator()
    image_url = image_generator.generate_image()
    image_generator.download_and_save_image(image_url)
    image_generator.display_image()

import asyncio
import os
import random
import string
from io import BytesIO
from pathlib import Path
from typing import Optional, Literal

import requests
from PIL import Image
from dotenv import load_dotenv
from openai import AsyncOpenAI

from jonbot import logger
from jonbot.system.path_getters import get_base_data_folder_path


class ImageGenerator:
    def __init__(self):
        self.latest_image_path = None
        self.image_save_path = Path(get_base_data_folder_path()) / "generated_images"
        load_dotenv()
        # self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def generate_image(self,
                             prompt: str = "an otherworldly entity, madness to behold (but otherwise kuwaii af)",
                             size: Optional[
                                 Literal["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"]] = "1024x1024",
                             quality: Literal["standard", "hd"] = "hd",
                             model: str = "dall-e-3",
                             style: Literal["vivid", "natural"] = "vivid",
                             n: int = 1):
        if model == "dall-e-3" and not n == 1:
            logger.warning(f"Model {model} does not support n={n} > 1. Setting n=1")
            n = 1

        if model == "dall-e-2":
            # TODO - do stuff to make things compatible with dall-e-2
            pass

        response = await self.client.images.generate(model=model,
                                                     prompt=prompt,
                                                     size=size,
                                                     quality=quality,
                                                     style=style,
                                                     n=n)
        filename = await self.get_file_name_from_prompt(prompt)
        self.download_and_save_image(url=response.data[0].url, filename=filename)
        return response.data[0].url

    def download_and_save_image(self, url: str, filename: str):
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        self.image_save_path.mkdir(parents=True, exist_ok=True)  # creates directory if it doesn't exist
        self.latest_image_path = self.image_save_path / filename
        img.save(self.latest_image_path)

    async def get_file_name_from_prompt(self, prompt: str) -> str:
        logger.info(f"Generating filename from prompt: {prompt}")
        completion = await self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": "Generate a highly condensed but descriptive filename (formated in `snake_case`) based on this prompt"},
                {"role": "user", "content": prompt},
            ]
        )
        filename = "generated_image"
        if completion.choices[0].message.content != "":
            filename = completion.choices[0].message.content.split(".")[0]
            filename = filename.replace(" ", "_")
            filename = filename.replace("\n", "")
            filename = filename.replace(":", "")

        # generate random 6 digit hex string
        random_hex_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        filename += "_" + random_hex_string + ".png"
        logger.info(f"Generated filename: {filename}")
        return filename

    def display_image(self):
        if os.name == 'nt':
            os.system(f"start {str(self.latest_image_path)}")
        else:
            os.system(f"xdg-open {str(self.latest_image_path)}")


if __name__ == '__main__':
    image_generator = ImageGenerator()
    image_url = asyncio.run(image_generator.generate_image())
    image_generator.display_image()

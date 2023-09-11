from typing import Optional

import discord
from pydantic import BaseModel


class DiscordUserID(BaseModel):
    id: int = 0
    name: Optional[str]
    discriminator: Optional[str]
    display_name: Optional[str]

    @classmethod
    def from_message(cls, message: discord.Message):
        return cls(
            id=message.author.id,
            name=message.author.name,
            discriminator=message.author.discriminator,
            display_name=message.author.display_name,
        )

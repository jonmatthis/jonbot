from typing import Optional

import discord
from pydantic import BaseModel


class DiscordID(BaseModel):
    id: int = 0
    name: Optional[str]
    discriminator: Optional[str]
    display_name: Optional[str]

    @classmethod
    def from_message(cls, message: discord.Message):
        return cls(id=message.author.id,
                   name=message.author.name,
                   discriminator=message.author.discriminator,
                   display_name=message.author.display_name)


class TelegramID(BaseModel):
    id: int = 0


class UserID(BaseModel):
    uuid: str
    discord_id: Optional[DiscordID]
    telegram_id: Optional[TelegramID]

    def __init__(self, uuid: str,
                 discord_id: Optional[DiscordID] = None,
                 telegram_id: Optional[TelegramID] = None, ):
        super().__init__()
        self.uuid = uuid

        if not discord_id and not telegram_id:
            raise ValueError("At least one of `discord_id` or `telegram_id` must be provided.")

        self.discord_id = discord_id if discord_id else DiscordID()
        self.telegram_id = telegram_id if telegram_id else TelegramID()

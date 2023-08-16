from typing import Optional

from pydantic import BaseModel

from jonbot.models.discord_stuff.discord_id import DiscordUserID


class TelegramUserID(BaseModel):
    id: int = 0


class UserID(BaseModel):
    uuid: str
    discord_id: Optional[DiscordUserID]
    telegram_id: Optional[TelegramUserID]

    def __init__(self, uuid: str,
                 discord_id: Optional[DiscordUserID] = None,
                 telegram_id: Optional[TelegramUserID] = None, ):
        super().__init__()
        self.uuid = uuid

        if not discord_id and not telegram_id:
            raise ValueError("At least one of `discord_id` or `telegram_id` must be provided.")

        self.discord_id = discord_id if discord_id else DiscordUserID()
        self.telegram_id = telegram_id if telegram_id else TelegramUserID()

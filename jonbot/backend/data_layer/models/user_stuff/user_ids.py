from typing import Optional

from pydantic import BaseModel

from jonbot.backend.data_layer.models.discord_stuff.discord_id import DiscordUserID


class UserID(BaseModel):
    uuid: str
    discord_id: Optional[DiscordUserID]

    def __init__(
            self,
            uuid: str,
            discord_id: DiscordUserID,
    ):
        super().__init__()
        self.uuid = uuid
        self.discord_id = discord_id

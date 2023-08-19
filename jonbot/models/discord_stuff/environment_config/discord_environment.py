import os
from typing import List, Dict, Any, Union, Optional

import toml
from pydantic import BaseModel

from jonbot import get_logger
from jonbot.system.environment.bot_tomls.get_bot_config_toml_path import get_bot_config_toml_path

logger = get_logger()


class DiscordEnvironmentConfig(BaseModel):
    _BOT_NICK_NAME: str
    _DISCORD_TOKEN: str
    _DEBUG_SERVER_ID: Optional[str]
    _ALLOWED_SERVERS: List[str]
    _DIRECT_MESSAGES_ALLOWED: bool
    _SERVERS_DETAILS: Dict[str, Any]
    _OWNER_IDS: List[str]

    @classmethod
    def configure(cls,
                  bot_name_or_index: Union[str, int] = 0):

        BOT_NICK_NAMES = os.getenv("BOT_NICK_NAMES").split(",")

        cls._BOT_NICK_NAME = None

        if isinstance(bot_name_or_index, int):
            cls._BOT_NICK_NAME = BOT_NICK_NAMES[bot_name_or_index]
        elif isinstance(bot_name_or_index, str):
            cls._BOT_NICK_NAME = bot_name_or_index
            assert cls._BOT_NICK_NAME in BOT_NICK_NAMES, f"Bot nick name {cls._BOT_NICK_NAME} not found in {BOT_NICK_NAMES}"

        if cls._BOT_NICK_NAME is None:
            raise EnvironmentError(f"Unable to configure the Discord bot with bot_name_or_index: `{bot_name_or_index}`")

        config_path = get_bot_config_toml_path(bot_nick_name=cls._BOT_NICK_NAME)

        config = toml.load(config_path)

        # Extract the desired values.
        assert config.get(
            "BOT_NICK_NAME") == cls._BOT_NICK_NAME, f"Bot nick name doesn't match what's in {str(config_path)}"

        cls._DISCORD_TOKEN = config.get("DISCORD_TOKEN")
        if cls._DISCORD_TOKEN is None:
            raise ValueError("`discord_token` not found in the TOML config!")

        cls._ALLOWED_SERVERS = config.get("ALLOWED_SERVERS")
        if not cls._ALLOWED_SERVERS:
            raise ValueError("ALLOWED_SERVERS not found or is empty in the TOML config!")

        cls._OWNER_IDS = config.get("OWNER_IDS")
        if not cls._OWNER_IDS:
            raise ValueError("owner_ids not found or is empty in the TOML config!")

        cls._DIRECT_MESSAGES_ALLOWED = config.get("DIRECT_MESSAGES_ALLOWED")
        if cls._DIRECT_MESSAGES_ALLOWED is None:
            raise ValueError("DIRECT_MESSAGES_ALLOWED not found in the TOML config!")

        cls._SERVERS_DETAILS = {}
        for SERVER_NAME in cls._ALLOWED_SERVERS:
            cls._SERVERS_DETAILS[SERVER_NAME] = config.get(SERVER_NAME, {})

        return cls(
            _BOT_NICK_NAME=cls._BOT_NICK_NAME,
            _DISCORD_TOKEN=cls._DISCORD_TOKEN,
            _ALLOWED_SERVERS=cls._ALLOWED_SERVERS,
            _DIRECT_MESSAGES_ALLOWED=cls._DIRECT_MESSAGES_ALLOWED,
            _SERVERS_DETAILS=cls._SERVERS_DETAILS,
            _OWNER_IDS=cls._OWNER_IDS
        )

    @property
    def BOT_NICK_NAME(self) -> str:
        return self._BOT_NICK_NAME

    @property
    def DISCORD_TOKEN(self) -> str:
        return self._DISCORD_TOKEN

    @property
    def ALLOWED_SERVERS(self) -> List[str]:
        return self._ALLOWED_SERVERS

    @property
    def DIRECT_MESSAGES_ALLOWED(self) -> bool:
        return self._DIRECT_MESSAGES_ALLOWED

    @property
    def SERVERS_DETAILS(self) -> dict:
        return self._SERVERS_DETAILS

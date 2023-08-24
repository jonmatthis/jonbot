import os
from typing import List, Dict, Any, Union, Optional

import toml
from pydantic import BaseModel

from jonbot import get_logger
from jonbot.system.environment.bot_tomls.get_bot_config_toml_path import (
    get_bot_config_toml_path,
)

logger = get_logger()


class BotConfigError(Exception):
    pass


class MissingTokenError(BotConfigError):
    pass


class MissingServerDetailsError(BotConfigError):
    pass


class DiscordEnvironmentConfig(BaseModel):
    """
    Configuration model for the Discord bot, retrieving data from
    environment variables and TOML files.
    """

    _IS_LOCAL: bool
    _BOT_NICK_NAME: str
    _DISCORD_TOKEN: str
    _DEBUG_SERVER_ID: Optional[str]
    _ALLOWED_SERVERS: List[str]
    _DIRECT_MESSAGES_ALLOWED: bool
    _SERVERS_DETAILS: Dict[str, Any]
    _OWNER_IDS: List[str]

    @classmethod
    def configure(
        cls, bot_name_or_index: Union[str, int] = 0
    ) -> "DiscordEnvironmentConfig":
        """
        Configures the environment settings based on the provided bot name or index.
        Fetches the corresponding settings from environment variables and TOML file.
        """
        cls._IS_LOCAL = not os.getenv("IS_DOCKER")

        BOT_NICK_NAMES = os.getenv("BOT_NICK_NAMES").split(",")

        if isinstance(bot_name_or_index, str) and bot_name_or_index in BOT_NICK_NAMES:
            cls._BOT_NICK_NAME = bot_name_or_index
        elif isinstance(bot_name_or_index, int) and 0 <= bot_name_or_index < len(
            BOT_NICK_NAMES
        ):
            cls._BOT_NICK_NAME = BOT_NICK_NAMES[bot_name_or_index]
        else:
            raise EnvironmentError(
                f"Unable to configure the Discord bot with bot_name_or_index: `{bot_name_or_index}`"
            )

        config_path = get_bot_config_toml_path(bot_nick_name=cls._BOT_NICK_NAME)
        config = toml.load(config_path)

        if config.get("BOT_NICK_NAME") != cls._BOT_NICK_NAME:
            raise BotConfigError(
                f"Bot nick name doesn't match what's in {str(config_path)}"
            )

        cls._DISCORD_TOKEN = config.get("DISCORD_TOKEN", None)
        if not cls._DISCORD_TOKEN:
            raise MissingTokenError("`discord_token` not found in the TOML config!")

        cls._ALLOWED_SERVERS = config.get("ALLOWED_SERVERS", [])
        if not cls._ALLOWED_SERVERS:
            raise MissingServerDetailsError(
                "ALLOWED_SERVERS not found or is empty in the TOML config!"
            )

        cls._OWNER_IDS = config.get("OWNER_IDS", [])
        if not cls._OWNER_IDS:
            raise BotConfigError("OWNER_IDS not found or is empty in the TOML config!")

        cls._DIRECT_MESSAGES_ALLOWED = config.get("DIRECT_MESSAGES_ALLOWED", False)

        cls._SERVERS_DETAILS = {
            SERVER_NAME: config.get(SERVER_NAME, {})
            for SERVER_NAME in cls._ALLOWED_SERVERS
        }

        return cls(
            _BOT_NICK_NAME=cls._BOT_NICK_NAME,
            _DISCORD_TOKEN=cls._DISCORD_TOKEN,
            _ALLOWED_SERVERS=cls._ALLOWED_SERVERS,
            _DIRECT_MESSAGES_ALLOWED=cls._DIRECT_MESSAGES_ALLOWED,
            _SERVERS_DETAILS=cls._SERVERS_DETAILS,
            _OWNER_IDS=cls._OWNER_IDS,
        )

    @property
    def IS_LOCAL(self) -> bool:
        return self._IS_LOCAL

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
    def SERVERS_DETAILS(self) -> Dict[str, Any]:
        return self._SERVERS_DETAILS

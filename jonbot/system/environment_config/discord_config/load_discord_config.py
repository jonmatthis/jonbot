import os
from pathlib import Path
from typing import Union, List, Any, Dict

import toml
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

DISCORD_CONFIG = None


def get_or_create_discord_config(bot_name_or_index: Union[str, int] = None):
    global DISCORD_CONFIG
    if DISCORD_CONFIG is None:

        if bot_name_or_index is None:
            raise ValueError("bot_name_or_index must be specified when creating the first DiscordConfig instance!")

        DISCORD_CONFIG = DiscordConfig()
        DISCORD_CONFIG.configure(bot_name_or_index=bot_name_or_index)
    return DISCORD_CONFIG


class DiscordConfig(BaseModel):
    _BOT_NICK_NAME: str = None
    _ALLOWED_SERVERS: List[str] = None
    _DIRECT_MESSAGES_ALLOWED: bool = None
    _SERVERS_DETAILS: Dict[str, Any] = None

    @classmethod
    def configure(cls, bot_name_or_index: Union[str, int] = 0):

        bot_nick_names = os.getenv("BOT_NICK_NAMES").split(",")

        cls._BOT_NICK_NAME = None

        if isinstance(bot_name_or_index, int):
            cls._BOT_NICK_NAME = bot_nick_names[bot_name_or_index]
        elif isinstance(bot_name_or_index, str):
            cls._BOT_NICK_NAME = bot_name_or_index
            assert cls._BOT_NICK_NAME in bot_nick_names, f"Bot nick name {cls._BOT_NICK_NAME} not found in {bot_nick_names}"

        if cls._BOT_NICK_NAME is None:
            raise EnvironmentError(f"Unable to configure the Discord bot with bot_name_or_index: `{bot_name_or_index}`")

        config_path = Path(__file__).parent / "bot_tomls" / f"{cls._BOT_NICK_NAME}_config.toml"
        config = toml.load(config_path.resolve())

        # Extract the desired values.
        assert config.get(
            "bot_nick_name") == cls._BOT_NICK_NAME, f"Bot nick name doesn't match what's in {str(config_path)}"

        cls._DISCORD_TOKEN = config.get("discord_token")
        if cls._DISCORD_TOKEN is None:
            raise ValueError("`discord_token` not found in the TOML config!")

        cls._ALLOWED_SERVERS = config.get("allowed_servers")
        if not cls._ALLOWED_SERVERS:
            raise ValueError("allowed_servers not found or is empty in the TOML config!")

        cls._DIRECT_MESSAGES_ALLOWED = config.get("direct_messages_allowed")
        if cls._DIRECT_MESSAGES_ALLOWED is None:
            raise ValueError("direct_messages_allowed not found in the TOML config!")

        cls._SERVERS_DETAILS = {}
        for server_name in cls._ALLOWED_SERVERS:
            cls._SERVERS_DETAILS[server_name] = config.get(server_name, {})

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

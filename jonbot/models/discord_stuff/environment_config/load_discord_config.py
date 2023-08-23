from typing import Union

from dotenv import load_dotenv

from jonbot.models.discord_stuff.environment_config.discord_environment import (
    DiscordEnvironmentConfig,
)

load_dotenv()

from jonbot import get_jonbot_logger

logger = get_jonbot_logger()

_DISCORD_ENVIRONMENT_CONFIG = None


def get_or_create_discord_environment_config(bot_name_or_index: Union[str, int] = None):
    global _DISCORD_ENVIRONMENT_CONFIG

    if _DISCORD_ENVIRONMENT_CONFIG is not None:
        return _DISCORD_ENVIRONMENT_CONFIG

    if bot_name_or_index is None:
        raise ValueError(
            "bot_name_or_index must be specified when creating the first DiscordConfig instance!"
        )

    try:
        _DISCORD_ENVIRONMENT_CONFIG = DiscordEnvironmentConfig.configure(
            bot_name_or_index=bot_name_or_index
        )
    except Exception as e:
        logger.exception("Error creating DISCORD_ENVIRONMENT_CONFIG.")
        raise

    return _DISCORD_ENVIRONMENT_CONFIG

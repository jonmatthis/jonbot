import discord

from jonbot import logger
from jonbot.backend.data_layer.models.discord_stuff.environment_config.load_discord_config import \
    get_or_create_discord_environment_config


def allowed_to_reply_in_channel(channel: discord.TextChannel) -> bool:
    try:
        discord_config = get_or_create_discord_environment_config()

        # Handle DMs
        if channel.type == discord.ChannelType.private:
            logger.trace(
                f"Channel `{channel}`is allowed to be handled by the bot {discord_config.BOT_NICK_NAME} (reason: DM)"
            )
            return discord_config.DIRECT_MESSAGES_ALLOWED

        # Handle server messages
        if "thread" in channel.type.name:
            channel_id = channel.parent.id
        else:
            channel_id = channel.id

        server_data = None
        for server_name, details in discord_config.SERVERS_DETAILS.items():
            if channel.guild.id == details["SERVER_ID"]:
                server_data = details
                break

        if not server_data:
            logger.error(
                f"Message received from server {channel.guild.id} which is not in the list of allowed servers :O"
            )
            return False

        excluded_categories = server_data.get("EXCLUDED_CATEGORIES_IDS", [])
        if channel_id in excluded_categories:
            logger.debug(
                f"Channel `{channel}`is not allowed to be handled by the bot {discord_config.BOT_NICK_NAME} (reason: excluded category)"
            )
            return False
        excluded_channels = server_data.get("EXCLUDED_CHANNEL_IDS", [])
        if channel_id in excluded_channels:
            logger.debug(
                f"Channel `{channel}`is not allowed to be handled by the bot {discord_config.BOT_NICK_NAME} (reason: excluded channel)"
            )
            return False

        allowed_categories = server_data.get("ALLOWED_CATEGORY_IDS", [])
        if allowed_categories == ["ALL"]:
            logger.trace(
                f"Channel `{channel}`is allowed to be handled by the bot {discord_config.BOT_NICK_NAME} (reason: allowed categories = ALL)"
            )
            return True

        if channel.category_id in allowed_categories:
            logger.trace(
                f"Channel `{channel}`is allowed to be handled by the bot {discord_config.BOT_NICK_NAME} (reason: allowed category)"
            )
            return True

        allowed_channels = server_data.get("ALLOWED_CHANNEL_IDS", [])
        if allowed_channels == ["ALL"]:
            logger.trace(
                f"Channel `{channel}`is allowed to be handled by the bot {discord_config.BOT_NICK_NAME} (reason: allowed channels = ALL)"
            )
            return True

        if channel_id not in allowed_channels:
            logger.debug(
                f"Channel `{channel}`is not allowed to be handled by the bot {discord_config.BOT_NICK_NAME} (reason: not allowed channel)"
            )
            return False

        logger.trace(
            f"Channel `{channel}`is allowed to be handled by the bot {discord_config.BOT_NICK_NAME} (reason: passed all checks)"
        )
        return True

    except Exception as e:
        logger.error(f"Error while checking if message is allowed to be handled: {e}")
        logger.exception(e)
        raise e

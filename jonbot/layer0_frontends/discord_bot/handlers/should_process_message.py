import discord

from jonbot import get_logger
from jonbot.models.discord_stuff.environment_config.load_discord_config import get_or_create_discord_environment_config

logger = get_logger()

FINISHED_VOICE_RECORDING_PREFIX = "Finished! Recorded audio for"
TRANSCRIBED_AUDIO_PREFIX = "Transcribed audio for"
RESPONSE_INCOMING_TEXT = "response incoming..."
ERROR_MESSAGE_REPLY_PREFIX_TEXT =  f"Sorry, an error occurred while processing your request"



def this_message_is_from_a_bot(message: discord.Message) -> bool:
    # returns True if the author of the message is a bot
    return message.author.bot


def check_if_transcribed_audio_message(message: discord.Message) -> bool:
    return (message.content.startswith(TRANSCRIBED_AUDIO_PREFIX) or
            message.content.startswith(FINISHED_VOICE_RECORDING_PREFIX))


def should_reply(message: discord.Message,
                 bot_user_name: str) -> bool:

    if not allowed_to_reply(message):
        logger.debug(f"Message `{message.content}` was not handled by the bot {bot_user_name} (reason: not allowed to reply)")
        return False

    if this_message_is_from_a_bot(message):
        logger.debug(f"Message `{message.content}` was not handled by the bot {bot_user_name} (reason: bot message)")
        return False

    if message.author.name == bot_user_name:
        logger.debug(f"Message `{message.content}` was not handled by the bot {bot_user_name} (reason: self-generated message)")
        return False

    logger.debug(f"Message `{message.content}` will be handled by the bot {bot_user_name} (reason: passed all checks)")
    return True


def allowed_to_reply(message: discord.Message) -> bool:

    discord_config = get_or_create_discord_environment_config()
    logger.trace(f"Checking if message `{message.content}` is allowed to be handled by the bot {discord_config.BOT_NICK_NAME}")
    # Handle DMs
    if message.channel.type == discord.ChannelType.private:
        logger.trace(f"Message `{message.content}` is allowed to be handled by the bot {discord_config.BOT_NICK_NAME} (reason: DM)")
        return discord_config.DIRECT_MESSAGES_ALLOWED

    # Handle server messages
    server_data = None
    for server_name, details in discord_config.SERVERS_DETAILS.items():
        if message.guild.id == details['SERVER_ID']:

            server_data = details
            break


    if not server_data:
        logger.error(
            f"Message received from server {message.guild.id} which is not in the list of allowed servers :O")
        return False



    allowed_categories = server_data.get("ALLOWED_CATEGORY_IDS", [])
    if allowed_categories == ["ALL"]:
        logger.trace(f"Message `{message.content}` is allowed to be handled by the bot {discord_config.BOT_NICK_NAME} (reason: allowed categories = ALL)")
        return True

    if message.channel.category_id in allowed_categories:
        logger.trace(f"Message `{message.content}` is allowed to be handled by the bot {discord_config.BOT_NICK_NAME} (reason: allowed category)")
        return True

    allowed_channels = server_data.get("ALLOWED_CHANNEL_IDS", [])
    if allowed_channels == ["ALL"]:
        logger.trace(f"Message `{message.content}` is allowed to be handled by the bot {discord_config.BOT_NICK_NAME} (reason: allowed channels = ALL)")
        return True

    if message.channel.id not in allowed_channels:
        logger.debug(f"Message `{message.content}` is not allowed to be handled by the bot {discord_config.BOT_NICK_NAME} (reason: not allowed channel)")
        return False

    logger.trace(f"Message `{message.content}` is allowed to be handled by the bot {discord_config.BOT_NICK_NAME} (reason: passed all checks)")
    return True

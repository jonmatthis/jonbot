from pathlib import Path
from typing import Union

import discord

from jonbot import get_logger
from jonbot.layer2_core_processes.entrypoint_functions.database_actions import get_conversation_history
from jonbot.models.conversation_models import ChatRequest, ConversationHistory
from jonbot.models.database_request_response_models import ConversationHistoryRequest
from jonbot.models.discord_stuff.discord_message import DiscordMessageDocument
from jonbot.system.path_getters import get_sample_discord_message_json_path

logger = get_logger()


async def save_sample_discord_message(message: discord.Message) -> None:
    """
    Saves the given Discord message as a JSON file.

    Args:
        message (discord.Message): The Discord message to be saved.
    """
    message_document = await DiscordMessageDocument.from_discord_message(message=message)
    json_path = get_sample_discord_message_json_path()

    with open(json_path, 'w') as file:
        file.write(message_document.json())

    logger.info(f"Saved message to {json_path}")


def load_sample_discord_message_document(
        json_path: Union[str, Path] = get_sample_discord_message_json_path()) -> DiscordMessageDocument:
    with open(json_path, 'r') as file:
        json_content = file.read()

    return DiscordMessageDocument.parse_raw(json_content)


async def load_sample_conversation_history() -> ConversationHistory:
    sample_chat_request = load_sample_chat_request()
    conversation_history_request = ConversationHistoryRequest.from_chat_request(chat_request=sample_chat_request)
    conversation_history = await get_conversation_history(conversation_history_request=conversation_history_request)
    return conversation_history


def load_sample_chat_request():
    sample_discord_message_document = load_sample_discord_message_document()
    return ChatRequest.from_discord_message_document(message_document=sample_discord_message_document,
                                                     database_name="jonbot_database")


if __name__ == '__main__':
    from pprint import pprint

    pprint(load_sample_chat_request().dict())

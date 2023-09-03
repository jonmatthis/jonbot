from typing import List

import discord

from jonbot.layer1_api_interface.api_client.api_client import ApiClient
from jonbot.layer1_api_interface.api_routes import UPSERT_MESSAGES_ENDPOINT
from jonbot.models.database_request_response_models import UpsertDiscordMessagesRequest
from jonbot.models.discord_stuff.discord_message import DiscordMessageDocument
from jonbot.system.setup_logging.get_logger import get_jonbot_logger

logger = get_jonbot_logger()


class DiscordDatabaseOperations:
    def __init__(self, api_client: ApiClient, database_name: str):
        self._api_client = api_client
        self._database_name = database_name

    async def upsert_messages(self, messages: List[discord.Message]) -> bool:
        try:
            documents = [
                await DiscordMessageDocument.from_discord_message(message)
                for message in messages
            ]

            request = UpsertDiscordMessagesRequest.from_discord_message_documents(
                documents=documents, database_name=self._database_name
            )

            logger.info(
                f"Sending database upsert request for {len(request.data)} messages to database: {request.database_name}"
            )

            response = await self._api_client.send_request_to_api(
                endpoint_name=UPSERT_MESSAGES_ENDPOINT, data=request.dict()
            )
            if not response["success"]:
                raise Exception(
                    f"Error occurred while sending `upsert_messages` request for"
                    f" database: {self._database_name}  at endpoint: {UPSERT_MESSAGES_ENDPOINT}"
                )

        except Exception as e:
            logger.exception(e)
            raise

        logger.success(
            f"Successfully sent {len(request.data)} messages to database: {request.database_name}"
        )
        return response["success"]

import asyncio
from typing import List

import discord

from jonbot import get_logger
from jonbot.layer1_api_interface.api_client.api_client import ApiClient
from jonbot.layer1_api_interface.api_routes import UPSERT_MESSAGE_ENDPOINT
from jonbot.models.database_request_response_models import UpsertDiscordMessageRequest
from jonbot.models.discord_stuff.discord_message import DiscordMessageDocument

logger = get_logger()


class DiscordDatabaseOperations:
    def __init__(self, api_client: ApiClient,
                 database_name: str):
        self._api_client = api_client
        self._database_name = database_name

    async def upsert_messages(self,
                              messages: List[discord.Message]):
        for message in messages:
            document = await DiscordMessageDocument.from_discord_message(message)

            request = UpsertDiscordMessageRequest(database_name=self._database_name,
                                                  data=document,
                                                  query={"message_id": message.id}
                                                  )
            logger.info(
                f"Sending database upsert request for message content: `{request.data.content}` "
                f"with query: `{request.query}`")
            await self._api_client.send_request_to_api(endpoint_name=UPSERT_MESSAGE_ENDPOINT,
                                                       data=request.dict(),
                                                       )


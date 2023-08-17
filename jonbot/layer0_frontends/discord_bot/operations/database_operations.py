import discord

from jonbot import get_logger
from jonbot.layer1_api_interface.api_client.api_client import ApiClient
from jonbot.layer1_api_interface.routes import DATABASE_UPSERT_ENDPOINT
from jonbot.models.database_request_response_models import DatabaseUpsertRequest
from jonbot.models.discord_stuff.discord_message import DiscordMessageDocument

logger = get_logger()


class DatabaseOperations:
    def __init__(self, api_client: ApiClient,
                 database_name: str,
                 collection_name: str):
        self._api_client = api_client
        self._database_name = database_name
        self._collection_name = collection_name

    async def log_message_in_database(self,
                                      message: discord.Message):
        discord_message_document = await DiscordMessageDocument.from_message(message)

        database_upsert_request = DatabaseUpsertRequest(database_name=self._database_name,
                                                        collection_name=self._collection_name,
                                                        data=discord_message_document.dict(),
                                                        query={"message_id": discord_message_document.message_id},
                                                        )
        logger.info(
            f"Sending database upsert request for message content: {message.content} "
            f"with route: {discord_message_document.context_route_path}")
        response = await self._api_client.send_request_to_api(endpoint_name=DATABASE_UPSERT_ENDPOINT,
                                                              data=database_upsert_request.dict(),
                                                              )
        if not response["success"]:
            logger.error(f"Failed to log message in database!! \n\n response: \n {response}")

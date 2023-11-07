from typing import List

import discord

from jonbot.api_interface.api_client.api_client import ApiClient
from jonbot.api_interface.api_routes import UPSERT_MESSAGES_ENDPOINT, GET_CONTEXT_MEMORY_ENDPOINT, UPSERT_CHATS_ENDPOINT
from jonbot.backend.data_layer.models.context_route import ContextRoute
from jonbot.backend.data_layer.models.database_request_response_models import UpsertDiscordMessagesRequest, \
    ContextMemoryDocumentRequest, UpsertDiscordChatsRequest
from jonbot.backend.data_layer.models.discord_stuff.discord_chat_document import DiscordChatDocument
from jonbot.backend.data_layer.models.discord_stuff.discord_message_document import DiscordMessageDocument
from jonbot.system.setup_logging.get_logger import get_jonbot_logger

logger = get_jonbot_logger()


class DiscordDatabaseOperations:
    def __init__(self, api_client: ApiClient, database_name: str):
        self._api_client = api_client
        self._database_name = database_name

    async def upsert_messages(self, messages: List[discord.Message]) -> bool:
        if len(messages) == 0:
            raise ValueError("Cannot upsert 0 messages")
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
            logger.error(f"Error occurred while sending `upsert_messages` request for - Error: `{e}`")
            logger.exception(e)
            raise Exception

        logger.info(
            f"Successfully sent {len(request.data)} messages to database: {request.database_name}"
        )
        return response["success"]

    async def upsert_chats(self, chat_documents: List[DiscordChatDocument]) -> bool:
        if len(chat_documents) == 0:
            raise ValueError("Cannot upsert 0 chats")
        try:
            request = UpsertDiscordChatsRequest.from_discord_chat_documents(
                documents=chat_documents, database_name=self._database_name
            )

            logger.info(
                f"Sending database upsert request for {len(request.data)} messages to database: {request.database_name}"
            )

            response = await self._api_client.send_request_to_api(
                endpoint_name=UPSERT_CHATS_ENDPOINT, data=request.dict()
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

    async def get_context_memory_document(self, message: discord.Message):
        try:
            context_route = ContextRoute.from_discord_message(message=message)
            get_request = ContextMemoryDocumentRequest.build_get_request(
                context_route=context_route,
                database_name=self._database_name,
            )
            logger.info(
                f"Getting context memory document for context route: {context_route.dict()}"
            )
            response = await self._api_client.send_request_to_api(endpoint_name=GET_CONTEXT_MEMORY_ENDPOINT,
                                                                  data=get_request.dict(),
                                                                  method="GET")

            if not response:
                logger.warning(
                    f"Could not load context memory from database for context route: {context_route.dict()}"
                )
                return

            return response
        except Exception as e:
            logger.error(
                f"Error occurred while getting context memory document - Error: `{e}`")
            logger.exception(e)
            raise

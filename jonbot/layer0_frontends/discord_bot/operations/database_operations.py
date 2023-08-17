import discord

from jonbot import get_logger
from jonbot.layer1_api_interface.api_client.api_client import ApiClient
from jonbot.layer1_api_interface.routes import DATABASE_UPSERT_ENDPOINT
from jonbot.models.conversation_models import ConversationHistory, ChatMessage
from jonbot.models.context_models import ContextRoute
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

    async def update_conversation_history_in_database(self,
                                                      message: discord.Message):

        logger.info(f"Updating conversation history for message: {message.content}")
        conversation_history = await self.get_conversation_history_from_message(message=message)
        database_upsert_request = DatabaseUpsertRequest(database_name=self._database_name,
                                                        collection_name=self._collection_name,
                                                        data=conversation_history.dict(),
                                                        query={
                                                            "context_route_query": ContextRoute.from_discord_message(
                                                                message=message).query()},
                                                        )

        await self._api_client.send_request_to_api(endpoint_name=DATABASE_UPSERT_ENDPOINT,
                                                   data=database_upsert_request.dict())

        logger.info(
            f"Updated conversation history for context_route_key: {ContextRoute.from_discord_message(message=message)}")

    async def get_conversation_history_from_message(self,
                                                    message: discord.Message,
                                                    message_limit: int = None) -> ConversationHistory:
        logger.info(f"Getting conversation history for message: {message.content}")
        # Check if the message is in a thread
        if message.thread:
            message_history = message.thread.history(limit=message_limit, oldest_first=False)
        else:
            message_history = message.channel.history(limit=message_limit, oldest_first=False)

        conversation_history = ConversationHistory()

        async for msg in message_history:
            if msg.content:
                conversation_history.add_message(chat_message=ChatMessage.from_discord_message(message=msg))

        return conversation_history

    async def log_message_in_database(self,
                                      message: discord.Message):

        discord_message_document = await DiscordMessageDocument.from_message(message)

        database_upsert_request = DatabaseUpsertRequest(database_name=self._database_name,
                                                        collection_name=self._collection_name,
                                                        data=discord_message_document.dict(),
                                                        query={"context_route_query": ContextRoute.from_discord_message(
                                                            message)},

                                                        )
        logger.info(
            f"Sending database upsert request for message content: {message.content} "
            f"with route: {discord_message_document.context_route}")
        response = await self._api_client.send_request_to_api(endpoint_name=DATABASE_UPSERT_ENDPOINT,
                                                              data=database_upsert_request.dict(),
                                                              )
        if not response["success"]:
            logger.error(f"Failed to log message in database!! \n\n response: \n {response}")

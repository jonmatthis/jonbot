import discord

from jonbot import get_logger
from jonbot.layer1_api_interface.api_client.api_client import ApiClient
from jonbot.layer1_api_interface.routes import DATABASE_UPSERT_ENDPOINT
from jonbot.models.conversation_models import ContextRoute, ConversationHistory, ChatMessage
from jonbot.models.database_upsert_models import DatabaseUpsertRequest

logger = get_logger()

class DatabaseOperations:
    def __init__(self, api_client: ApiClient,
                 database_name: str,
                 collection_name: str):
        self._api_client = api_client
        self._database_name = database_name
        self._collection_name = collection_name

    async def log_message(self, message: discord.Message) -> None:
        """Logs a message in the database."""
        # Code for logging the message

    async def update_conversation_history_in_database(self,
                                                      message: discord.Message):

        conversation_history = await self.get_conversation_history_from_message(message=message)
        upsert_request = DatabaseUpsertRequest(database_name=self._database_name,
                                               collection_name=self._database_collection_name,
                                               data=conversation_history.dict(),
                                               query={"context_route_parent": ContextRoute.from_discord_message(
                                                   message=message).parent},
                                               )

        await self._api_client.send_request_to_api(endpoint_name=DATABASE_UPSERT_ENDPOINT,
                                             data=upsert_request.dict())

        logger.info(
            f"Updated conversation history for context_route_key: {ContextRoute.from_discord_message(message=message)}")
    async def get_conversation_history_from_message(self,
                                                    message: discord.Message,
                                                    message_limit: int = 99999) -> ConversationHistory:
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

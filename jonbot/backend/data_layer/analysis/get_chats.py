import asyncio
from typing import Dict, Any

from jonbot import logger
from jonbot.backend.data_layer.database.get_mongo_database_manager import get_mongo_database_manager
from jonbot.backend.data_layer.database.mongo_database import MongoDatabaseManager
from jonbot.system.environment_variables import CHATS_COLLECTION_NAME


async def get_chats(database_name: str,
                    mongo_database_manager: MongoDatabaseManager = None,
                    query: Dict = None,
                    collection_name: str = CHATS_COLLECTION_NAME) -> Dict[str, Dict[str, Any]]:
    try:
        if query is None:
            query = {}
        if mongo_database_manager is None:
            mongo_database_manager = await get_mongo_database_manager()

        logger.info(f"Getting collection: {collection_name} in database: {database_name}")
        collection = mongo_database_manager.get_collection(database_name=database_name,
                                                           collection_name=collection_name)

        logger.info(f"Querying collection: {collection_name} with query: {query}")
        chat_documents = await collection.find(query).to_list(length=None)
        chats = {}
        for chat_document in chat_documents:
            chat_context_query = chat_document['query']
            # chats[str(chat_context_query)] = DiscordChatDocument(**chat_document)
            chats[str(chat_context_query)] = chat_document
        logger.info(f"Found {len(chat_documents)} chat documents in  database: {database_name} with query: {query}")
        return chats
    except Exception as e:
        logger.error(f"Error getting chat documents for with query: {query}")
        logger.exception(e)
        raise e


if __name__ == "__main__":
    database_name_in = "classbot_database"
    server_id = 1150736235430686720

    chats_out = asyncio.run(get_chats(database_name=database_name_in,
                                      query={"server_id": server_id}))

import asyncio
import logging

from jonbot.backend.data_layer.database.get_or_create_mongo_database_manager import get_mongo_database_manager

logger = logging.getLogger(__name__)


async def summarize_chats(database_name: str,
                          channel_id: int):
    mongo_database = await get_mongo_database_manager()
    logger.info(f"Getting database: {database_name}")
    database = mongo_database.get_database(database_name)

    logger.info(f"Getting collection: raw_messages")
    collection = database.get_collection(f"raw_messages")
    logger.info(f"Searching for messages in channel: {channel_id}")

    pipeline = [
        {"$match": {"channel_id": channel_id}},
        {"$group": {"_id": "$author_id", "messages": {"$push": "$$ROOT"}}}
    ]

    grouped_messages = await collection.aggregate(pipeline).to_list(length=None)
    logger.info(f"Found {len(grouped_messages)} users")

    messages_by_user = {entry["_id"]: entry["messages"] for entry in grouped_messages}

    logger.info(f"Saving messages to database: {database_name}")


if __name__ == "__main__":
    database_name = "classbot_database"
    channel_id = 1151164504483315722
    asyncio.run(summarize_chats(database_name=database_name,
                                channel_id=channel_id))
    print("Done!")

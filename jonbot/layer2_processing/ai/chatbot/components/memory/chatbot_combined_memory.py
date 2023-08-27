from langchain.memory import CombinedMemory

from jonbot import get_logger
from jonbot.layer2_processing.ai.chatbot.components.memory.conversation_memory.conversation_memory import (
    ChatbotConversationMemory,
)
from jonbot.layer2_processing.backend_database_operator.backend_database_operator import (
    BackendDatabaseOperations,
)
from jonbot.models.context_route import ContextRoute

logger = get_logger()


class ChatbotCombinedMemory(CombinedMemory):
    @classmethod
    async def build(
        cls,
        database_operations: BackendDatabaseOperations,
        database_name: str,
        context_route: ContextRoute,
    ):
        memories = cls.configure_memories()

        memories = [
            ChatbotConversationMemory(
                database_operations=database_operations,
                database_name=database_name,
                context_route=context_route,
            ),
            # await ChatbotVectorStoreMemory.build(),
        ]

        return cls(memories=memories)

    # @staticmethod
    # async def configure_memories():
    #     for memory in self.memories:
    #         try:
    #             memory.configure_memories()
    #         except Exception as e:
    #             logger.exception(f"Error configuring memory: {str(e)}")
    #             logger.error(f"Memory: {memory} not configured!")
    #             continue

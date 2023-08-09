import logging
from typing import List

from langchain.memory import CombinedMemory
from langchain.schema import BaseMemory

from jonbot.layer2_core_processes.ai_chatbot.components.memory.sub_memory_builders.conversation_memory_builder import \
    ChatbotConversationMemoryBuilder
from jonbot.layer2_core_processes.ai_chatbot.components.memory.sub_memory_builders.vectorstore_memory_builder import \
    ChatbotVectorStoreMemoryBuilder
from jonbot.layer3_data_layer.data_models.conversation_models import ConversationHistory

logger = logging.getLogger(__name__)
CONVERSATION_HISTORY_MAX_TOKENS = 1000


class ChatbotMemoryBuilder(CombinedMemory):
    @classmethod
    async def build(cls,
                    conversation_history: ConversationHistory = None):
        memories = await cls._configure_memories()

        instance = cls(memories=memories)

        if conversation_history is not None:
            instance.load_memory_from_history(conversation_history=conversation_history)

        return instance

    @staticmethod
    async def _configure_memories(conversation_history: ConversationHistory = None) -> List[BaseMemory]:
        return [ChatbotConversationMemoryBuilder.build(conversation_history=conversation_history),
                await ChatbotVectorStoreMemoryBuilder.build()]

from typing import List

from langchain.memory import CombinedMemory
from langchain.schema import BaseMemory

from jonbot.layer2_core_processes.core.ai.components.memory.sub_memory_components.conversation_memory import \
    ChatbotConversationMemory
from jonbot.layer2_core_processes.core.ai.components.memory.sub_memory_components.vectorstore_memory import \
    ChatbotVectorStoreMemoryBuilder
from jonbot.models.conversation_models import ConversationHistory


class ChatbotMemory(CombinedMemory):
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
        return [ChatbotConversationMemory(),
                await ChatbotVectorStoreMemoryBuilder.build()]


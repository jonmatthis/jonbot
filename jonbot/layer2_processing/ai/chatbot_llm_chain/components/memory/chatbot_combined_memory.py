from typing import List

from langchain.memory import CombinedMemory
from langchain.schema import BaseMemory

from jonbot.layer2_processing.ai.chatbot_llm_chain.components.memory.conversation_memory.conversation_memory import (
    ChatbotConversationMemory,
)
from jonbot.layer2_processing.ai.chatbot_llm_chain.components.memory.vectorstore_memory.vectorstore_memory import (
    ChatbotVectorStoreMemoryBuilder,
)
from jonbot.models.conversation_models import MessageHistory


class ChatbotCombinedMemory(CombinedMemory):
    @classmethod
    async def build(cls, conversation_history: MessageHistory = None):
        memories = await cls._configure_memories()

        instance = cls(memories=memories)

        if conversation_history is not None:
            instance.load_memory_from_history(conversation_history=conversation_history)

        return instance

    @staticmethod
    async def _configure_memories(
        conversation_history: MessageHistory = None,
    ) -> List[BaseMemory]:
        return [
            ChatbotConversationMemory(),
            await ChatbotVectorStoreMemoryBuilder.build(),
        ]

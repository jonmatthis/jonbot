import logging
from typing import List

from langchain import OpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.memory import CombinedMemory, VectorStoreRetrieverMemory, ConversationSummaryBufferMemory
from langchain.schema import BaseMemory
from langchain.vectorstores import VectorStore, Chroma

from jonbot.layer3_data_layer.data_models.conversation_models import ConversationHistory
from jonbot.layer3_data_layer.system.filenames_and_paths import get_chroma_vector_store_path

logger = logging.getLogger(__name__)
CONVERSATION_HISTORY_MAX_TOKENS = 1000


class ChatbotVectorStoreMemory(VectorStoreRetrieverMemory):
    @classmethod
    async def create(cls):
        chroma_vector_store = await cls._create_vector_store()

        retriever = chroma_vector_store.as_retriever(search_kwargs=dict(k=1))

        return cls(retriever=retriever,
                   memory_key="vectorstore_memory",
                   input_key="human_input",
                   )

    @staticmethod
    async def _create_vector_store(collection_name: str = "test_collection") -> VectorStore:
        return Chroma(
            embedding_function=OpenAIEmbeddings(),
            collection_name=collection_name,
            persist_directory=str(get_chroma_vector_store_path()),
        )


class ChatbotConversationMemory(ConversationSummaryBufferMemory):
    @classmethod
    def create(cls, conversation_history: ConversationHistory = None):
        instance = cls(memory_key="chat_memory",
                       input_key="human_input",
                       llm=OpenAI(temperature=0),
                       max_token_limit=CONVERSATION_HISTORY_MAX_TOKENS)

        if conversation_history is not None:
            instance.load_memory_from_history(conversation_history=conversation_history)

        return instance

    def load_memory_from_history(self,
                                 conversation_history=ConversationHistory,
                                 max_tokens=CONVERSATION_HISTORY_MAX_TOKENS):
        logger.info(f"Loading {len(conversation_history.get_all_messages())} messages into memory.")

        for chat_message in conversation_history.get_all_messages():
            if chat_message.speaker.type == "human":
                self.chat_memory.add_user_message(
                    f"On {str(chat_message.timestamp)} the human {chat_message.speaker.name} said: {chat_message.message}")
            elif chat_message.speaker.type == "bot":
                self.chat_memory.add_ai_message(
                    f"On {str(chat_message.timestamp)}, the AI (you) {chat_message.speaker.name} said: {chat_message.message}")
            if self.llm.get_num_tokens_from_messages(
                    messages=self.chat_memory.messages) > max_tokens:
                self.prune()
                break



class ChatbotMemory(CombinedMemory):
    @classmethod
    async def create(cls,
                     conversation_history: ConversationHistory = None):
        memories = await cls._configure_memories()

        instance = cls(memories=memories)

        if conversation_history is not None:
            instance.load_memory_from_history(conversation_history=conversation_history)

        return instance

    @staticmethod
    async def _configure_memories(conversation_history: ConversationHistory = None) -> List[BaseMemory]:
        return [ChatbotConversationMemory.create(conversation_history=conversation_history),
                await ChatbotVectorStoreMemory.create()]

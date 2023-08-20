
from typing import List, Union

from langchain.memory import ConversationSummaryBufferMemory
from langchain.schema import HumanMessage, AIMessage

from jonbot import get_logger
from jonbot.models.context_memory_document import ContextMemoryDocument
from jonbot.models.memory_config import ChatbotConversationMemoryConfig

logger = get_logger()


class ChatbotConversationMemory(ConversationSummaryBufferMemory):
    def __init__(self, config: ChatbotConversationMemoryConfig = None):
        if config is None:
            config = ChatbotConversationMemoryConfig()

        super().__init__(
            memory_key=config.memory_key,
            input_key=config.input_key,
            llm=config.llm,
            return_messages=config.return_messages,
            max_token_limit=config.max_token_limit,
        )

        self.prompt = config.summary_prompt

    @property
    def tokens_in_summary(self):
        return self.llm.get_num_tokens_from_messages(self.buffer)
    def load_context_memory(self, context_memory_document: ContextMemoryDocument):

        self.chat_memory.messages = self.load_messages_from_context_memory(context_memory_document)
        self.moving_summary_buffer = context_memory_document.summary
        self.prompt = context_memory_document.summary_prompt
        logger.debug(f"Loaded context memory from database: {self.buffer}")

    @staticmethod
    def load_messages_from_context_memory(context_memory_document) -> List[Union[HumanMessage, AIMessage]]:
        messages = []
        for message_dict in context_memory_document.message_buffer:
            if message_dict["additional_kwargs"]["type"] == "human":
                messages.append(HumanMessage(**message_dict))
            elif message_dict["additional_kwargs"]["type"] == "ai":
                messages.append(AIMessage(**message_dict))
        return messages

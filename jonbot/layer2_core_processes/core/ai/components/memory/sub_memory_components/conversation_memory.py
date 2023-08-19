from langchain.memory import ConversationSummaryBufferMemory

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

    def load_context_memory(self, context_memory_document: ContextMemoryDocument):
        self.chat_memory.messages = context_memory_document.buffer
        self.moving_summary_buffer = context_memory_document.summary
        self.prompt = context_memory_document.summary_prompt
        logger.debug(f"Loaded context memory from database: {self.buffer}")

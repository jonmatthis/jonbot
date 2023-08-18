from typing import Any

from langchain import OpenAI, PromptTemplate
from langchain.memory import ConversationSummaryBufferMemory
from pydantic import BaseModel

from jonbot import get_logger
from jonbot.layer2_core_processes.core.ai.components.memory.sub_memory_components.conversation_summary_prompt_templates import \
    CONVERSATION_SUMMARY_PROMPT

logger = get_logger()

CONVERSATION_HISTORY_MAX_TOKENS = 1000


class ChatbotConversationMemoryConfig(BaseModel):
    memory_key: str = "chat_memory"
    input_key: str = "human_input"
    llm: Any = OpenAI(temperature=0)
    return_messages: bool = True
    max_token_limit: int = CONVERSATION_HISTORY_MAX_TOKENS
    summary_prompt: PromptTemplate = CONVERSATION_SUMMARY_PROMPT


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

from typing import Any

from langchain import OpenAI
from langchain.llms.base import LLM, BaseLLM
from langchain.memory import ConversationSummaryBufferMemory
from pydantic import BaseModel

from jonbot import get_logger
from jonbot.layer2_core_processes.core.ai.components.memory.sub_memory_components.prompt_templates import \
    CUSTOM_SUMMARY_PROMPT

logger = get_logger()

CONVERSATION_HISTORY_MAX_TOKENS = 1000




class ChatbotConversationMemoryBuilder(ConversationSummaryBufferMemory):
    memory_key: str = "chat_memory"
    input_key: str = "human_input"
    llm: Any = OpenAI(temperature=0)
    return_messages: bool = True
    max_token_limit: int = 1000
    summary_prompt: str = CUSTOM_SUMMARY_PROMPT
    @classmethod
    def build(cls,
              **kwargs):
        instance = cls(**kwargs)
        instance.prompt = instance.summary_prompt
        return instance

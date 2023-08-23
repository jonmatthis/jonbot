from typing import Any

from langchain import OpenAI, PromptTemplate
from pydantic import BaseModel

from jonbot.layer2_processing.ai.chatbot_llm_chain.components.memory.conversation_memory.conversation_summary_prompt_templates import (
    CONVERSATION_SUMMARY_PROMPT,
)

CONVERSATION_HISTORY_MAX_TOKENS = 1000


class ChatbotConversationMemoryConfig(BaseModel):
    memory_key: str = "chat_memory"
    input_key: str = "human_input"
    llm: Any = OpenAI(temperature=0)
    return_messages: bool = True
    max_token_limit: int = CONVERSATION_HISTORY_MAX_TOKENS
    summary_prompt: PromptTemplate = CONVERSATION_SUMMARY_PROMPT

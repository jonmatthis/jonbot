from typing import Any

from langchain import PromptTemplate
from langchain.chat_models import ChatOpenAI
from pydantic import BaseModel

from jonbot.backend.ai.chatbot.components.memory.conversation_memory.conversation_summary_prompt_templates import (
    CONVERSATION_SUMMARY_PROMPT,
)

CONVERSATION_HISTORY_MAX_TOKENS = 1000


class ChatbotConversationMemoryConfig(BaseModel):
    memory_key: str = "chat_memory"
    input_key: str = "human_input"
    llm: Any = ChatOpenAI(temperature=0,
                          model_name="gpt-3.5-turbo-16k", )
    return_messages: bool = True
    max_token_limit: int = CONVERSATION_HISTORY_MAX_TOKENS
    summary_prompt: PromptTemplate = CONVERSATION_SUMMARY_PROMPT

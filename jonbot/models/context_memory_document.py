from typing import List, Any

from langchain import PromptTemplate
from langchain.schema import HumanMessage, AIMessage
from pydantic import BaseModel

from jonbot.layer2_processing.core_processing.ai.components.memory.conversation_memory.conversation_memory import \
    ChatbotConversationMemory
from jonbot.models.context_route import ContextRoute


class ContextMemoryDocument(BaseModel):
    context_route: ContextRoute
    message_buffer: List[Any] = []
    summary: str = ""
    summary_prompt: PromptTemplate = None
    tokens_count: int = 0

    @classmethod
    def build(cls, context_route: ContextRoute, memory: ChatbotConversationMemory):
        return cls(context_route=context_route,
                   message_buffer=cls._build_message_buffer(memory.buffer),
                   summary=memory.moving_summary_buffer,
                   summary_prompt=memory.prompt,
                   tokens_count=memory.token_count)
    @property
    def query(self):
        return self.context_route.as_query

    @property
    def message_uuids(self):
        message_uuids = [message["additional_kwargs"]["uuid"] for message in self.memory.buffer],
        return message_uuids

    @staticmethod
    def _build_message_buffer(message_buffer: List[Any]):
        buffer_out = []
        for message in message_buffer:
            if isinstance(message, HumanMessage):
                msg = message.dict()
                msg["additional_kwargs"]["type"] = "human"
                buffer_out.append(msg)
            elif isinstance(message, AIMessage):
                msg = message.dict()
                msg["additional_kwargs"]["type"] = "ai"
                buffer_out.append(msg)
            else:
                raise Exception(f"Invalid message type: {type(message)}")
        return buffer_out
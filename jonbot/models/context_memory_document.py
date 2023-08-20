from typing import List, Any, Optional

from langchain import PromptTemplate
from langchain.schema import HumanMessage, AIMessage
from pydantic import BaseModel

from jonbot.layer2_processing.core_processing.ai.chatbot_llm_chain.components.memory.conversation_memory.conversation_memory import \
    ChatbotConversationMemory
from jonbot.models.context_route import ContextRoute


class ContextMemoryDocument(BaseModel):
    context_route: ContextRoute
    context_route_full_path: str
    context_route_friendly_path: str
    message_buffer: List[Any] = None
    message_uuids: List[str] = None
    summary: str = ""
    summary_prompt: PromptTemplate = None
    tokens_count: int = 0

    query: dict
    server_name: str
    server_id: int
    channel_name: str
    channel_id: int
    thread_name: Optional[str]
    thread_id: Optional[int]

    @classmethod
    def build_empty(cls,
                    context_route: ContextRoute):
        return cls(context_route=context_route,
                   context_route_full_path=context_route.full_path,
                   context_route_friendly_path=context_route.friendly_path,
                   message_buffer=[],
                   summary="",
                   summary_prompt=None,
                   tokens_count=0,
                   query=context_route.as_query,
                   **context_route.as_flat_dict)

    @classmethod
    def build(cls,
              context_route: ContextRoute,
              memory: ChatbotConversationMemory):
        instance = cls.build_empty(context_route=context_route)
        instance.update_from_memory(memory=memory)
        return instance

    def update_from_memory(self,
                           memory: ChatbotConversationMemory):
        self.message_buffer = self._build_message_buffer(memory.buffer)
        self.message_uuids = [message["additional_kwargs"]["uuid"] for message in self.message_buffer],
        self.summary = memory.moving_summary_buffer
        self.summary_prompt = memory.prompt
        self.tokens_count = memory.token_count



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

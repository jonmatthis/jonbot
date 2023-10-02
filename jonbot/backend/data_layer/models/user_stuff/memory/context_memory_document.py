from typing import Optional

from pydantic import BaseModel

from jonbot.backend.data_layer.models.context_route import ContextRoute
from jonbot.backend.data_layer.models.user_stuff.memory.chat_memory_message_buffer import ChatMemoryMessageBuffer


class ContextMemoryDocument(BaseModel):
    context_route: ContextRoute
    context_route_full_path: str
    context_route_friendly_path: str
    # summary_prompt: Optional[PromptTemplate]

    query: dict
    server_name: str
    server_id: int
    channel_name: str
    channel_id: int
    thread_name: Optional[str]
    thread_id: Optional[int]

    chat_memory_message_buffer: Optional[ChatMemoryMessageBuffer]
    # message_uuids: List[str] = None
    # summary: str = ""
    tokens_count: int = 0

    @classmethod
    def build_empty(cls,
                    context_route: ContextRoute):
        # summary_prompt: Optional[PromptTemplate]):
        return cls(
            context_route=context_route,
            context_route_full_path=context_route.full_path,
            context_route_friendly_path=context_route.friendly_path,
            # summary="",
            # summary_prompt=summary_prompt,
            tokens_count=0,
            query=context_route.as_query,
            **context_route.as_flat_dict,
        )

    def update(
            self,
            chat_memory_message_buffer: ChatMemoryMessageBuffer,
            # summary: str,
            tokens_count: int,
    ):
        self.chat_memory_message_buffer = chat_memory_message_buffer
        # self.summary = summary
        self.tokens_count = tokens_count

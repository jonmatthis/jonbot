from typing import List, Optional, Union

from langchain import BasePromptTemplate, PromptTemplate
from langchain.schema import HumanMessage, AIMessage
from pydantic import BaseModel

from jonbot.models.context_route import ContextRoute


class ContextMemoryDocument(BaseModel):
    context_route: ContextRoute
    context_route_full_path: str
    context_route_friendly_path: str

    query: dict
    server_name: str
    server_id: int
    channel_name: str
    channel_id: int
    thread_name: Optional[str]
    thread_id: Optional[int]

    message_buffer: List[Union[HumanMessage, AIMessage]] = None
    # message_uuids: List[str] = None
    summary: str = ""
    summary_prompt: BasePromptTemplate = None
    tokens_count: int = 0

    @classmethod
    def build_empty(
        cls, context_route: ContextRoute, summary_prompt: Optional[PromptTemplate]
    ):
        return cls(
            context_route=context_route,
            context_route_full_path=context_route.full_path,
            context_route_friendly_path=context_route.friendly_path,
            query=context_route.as_query,
            **context_route.as_flat_dict,
            message_buffer=[],
            summary="",
            summary_prompt=summary_prompt,
            tokens_count=0,
        )

    def update(
        self,
        message_buffer: List[Union[HumanMessage, AIMessage]],
        summary: str,
        summary_prompt: PromptTemplate,
        tokens_count: int,
    ):
        for message in message_buffer:
            if isinstance(message, HumanMessage):
                message.additional_kwargs["type"] = "human"
            elif isinstance(message, AIMessage):
                message.additional_kwargs["type"] = "ai"
            else:
                raise ValueError(f"Message type not recognized: {message}")
        self.message_buffer = message_buffer
        self.summary = summary
        self.tokens_count = tokens_count
        self.summary_prompt = summary_prompt

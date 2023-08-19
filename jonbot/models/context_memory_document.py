from typing import List, Any

from langchain import PromptTemplate
from langchain.schema import BaseMessage
from pydantic import BaseModel

from jonbot.models.context_route import ContextRoute


class ContextMemoryDocument(BaseModel):
    context_route: ContextRoute
    message_buffer: List[Any] = []
    message_uuids: List[str] = []
    summary: str = ""
    summary_prompt: PromptTemplate

    @property
    def message_uuids(self):
        message_uuids = [message["additional_kwargs"]["uuid"] for message in self.memory.buffer],
        return message_uuids



from typing import List, Any

from langchain import PromptTemplate
from langchain.schema import BaseMessage
from pydantic import BaseModel

from jonbot.models.context_route import ContextRoute


class ContextMemoryDocument(BaseModel):
    context_route: ContextRoute
    message_buffer: List[Any] = []
    summary: str = ""
    summary_prompt: PromptTemplate

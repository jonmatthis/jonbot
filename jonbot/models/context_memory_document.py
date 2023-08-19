from typing import List

from langchain import PromptTemplate
from langchain.schema import BaseMessage
from pydantic import BaseModel

from jonbot.models.context_route import ContextRoute
from jonbot.system.environment_variables import CONTEXT_MEMORIES_COLLECTION_NAME


class ContextMemoryDocument(BaseModel):
    context_route: ContextRoute
    buffer: List[BaseMessage] = []
    summary: str = ""
    summary_prompt: PromptTemplate
    context_memories_collection_name: str = CONTEXT_MEMORIES_COLLECTION_NAME

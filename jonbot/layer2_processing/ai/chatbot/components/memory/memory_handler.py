from typing import List

from langchain import BasePromptTemplate
from langchain.schema import BaseMessage
from pydantic import BaseModel

from jonbot import get_logger
from jonbot.layer2_processing.ai.chatbot.components.memory.conversation_memory.context_memory_handler import (
    ContextMemoryHandler,
)
from jonbot.layer2_processing.backend_database_operator.backend_database_operator import (
    BackendDatabaseOperations,
)
from jonbot.models.context_memory_document import ContextMemoryDocument
from jonbot.models.conversation_models import ChatRequest

logger = get_logger()


class MemoryHandler(BaseModel):
    context_memory_handler: ContextMemoryHandler

    @classmethod
    async def from_context_memory_handler(
        cls, context_memory_handler: ContextMemoryHandler
    ):
        return cls(context_memory_handler=context_memory_handler)

    @classmethod
    async def from_chat_request(
        cls, chat_request: ChatRequest, database_operations: BackendDatabaseOperations
    ):
        context_memory_handler = ContextMemoryHandler.build(
            chat_request=chat_request,
            database_operations=database_operations,
        )
        return cls(context_memory_handler=context_memory_handler)


    async def get_context_memory_document(self) -> ContextMemoryDocument:
        try:
            if self.get_context_memory_document() is None:
                return await self.context_memory_handler.get_context_memory_document()
            if self.get_context_memory_document() is None:
                raise Exception(
                    f"Failed to load context memory document from context memory handler: {self.context_memory_handler}"
                )
        except Exception as e:
            logger.exception(
                f"Error getting context memory document from context memory handler: {self.context_memory_handler}"
            )
            raise e

    async def update(self,
               message_buffer: List[BaseMessage],
               summary: str,
               token_count: int,
               summary_prompt: BasePromptTemplate):

        await self.context_memory_handler.update(message_buffer=message_buffer,
                                           summary=summary,
                                           token_count=token_count,
                                           summary_prompt=summary_prompt)

from typing import List, Any, Dict

from langchain.memory import ConversationSummaryBufferMemory
from langchain.schema import HumanMessage, AIMessage, BaseMessage

from jonbot import get_logger
from jonbot.layer2_processing.ai.chatbot.components.memory.memory_handler import (
    MemoryHandler,
)
from jonbot.models.context_memory_document import ContextMemoryDocument
from jonbot.models.memory_config import ChatbotConversationMemoryConfig

logger = get_logger()


class ChatbotConversationMemory(ConversationSummaryBufferMemory):
    memory_handler: MemoryHandler

    def __init__(
        self,
        memory_handler: MemoryHandler,
        config: ChatbotConversationMemoryConfig = None,
    ):
        if config is None:
            config = ChatbotConversationMemoryConfig()

        super().__init__(
            memory_key=config.memory_key,
            input_key=config.input_key,
            llm=config.llm,
            return_messages=config.return_messages,
            max_token_limit=config.max_token_limit,
            memory_handler=memory_handler,
        ),

        self.prompt = config.summary_prompt

    async def get_context_memory_document(self) -> ContextMemoryDocument:
        return await self.memory_handler.get_context_memory_document()

    @property
    def token_count(self) -> int:
        tokens_in_messages = self.llm.get_num_tokens_from_messages(self.buffer)
        tokens_in_summary = self.llm.get_num_tokens(self.moving_summary_buffer)
        return tokens_in_messages + tokens_in_summary

    async def configure_memory(self):
        document = await self.get_context_memory_document()
        if document:
            self._build_memory_from_context_memory_document(document=document)
        else:
            logger.warning(
                f"Context memory document is None, cannot build memory: {document}"
            )

    def _build_memory_from_context_memory_document(
        self, document: ContextMemoryDocument
    ):
        self._load_messages_from_message_buffer(buffer=document.message_buffer)

        # # self.message_uuids = [message["additional_kwargs"]["uuid"] for message in self.message_buffer],
        self.moving_summary_buffer = document.summary if document else ""
        self.prompt = document.summary_prompt

    def _load_messages_from_message_buffer(self, buffer: List[BaseMessage]):
        messages = []
        try:
            for message in buffer:
                if message.additional_kwargs["type"] == "human":
                    if isinstance(message, AIMessage):
                        logger.warning(
                            f"Message type is AIMessage but type is `human`: {message}"
                        )
                    messages.append(message)
                elif message.additional_kwargs["type"] == "ai":
                    if isinstance(message, HumanMessage):
                        logger.warning(
                            f"Message type is HumanMessage but type is `ai`: {message}"
                        )
                    messages.append(AIMessage(**message.dict()))
            self.chat_memory.messages = messages
        except Exception as e:
            logger.exception(e)
            raise

    async def update(self, inputs: Dict[str, Any], outputs: Dict[str, Any]):
        self.save_context(inputs=inputs, outputs=outputs)
        await self.memory_handler.update(
            message_buffer=self.buffer,
            summary=self.moving_summary_buffer,
            token_count=self.token_count,
            summary_prompt=self.prompt,
        )

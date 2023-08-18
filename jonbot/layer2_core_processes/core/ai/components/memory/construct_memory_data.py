import asyncio
from typing import List

from langchain import PromptTemplate
from langchain.schema import BaseMessage
from pydantic import BaseModel

from jonbot import get_logger
from jonbot.layer2_core_processes.core.ai.components.memory.sub_memory_components.conversation_memory import \
    ChatbotConversationMemory, CONVERSATION_HISTORY_MAX_TOKENS, ChatbotConversationMemoryConfig
from jonbot.layer2_core_processes.entrypoint_functions.database_actions import get_conversation_history, database_upsert
from jonbot.models.context_route import ContextRoute
from jonbot.models.conversation_models import ChatRequest, ConversationHistory
from jonbot.models.database_request_response_models import ConversationHistoryRequest, DatabaseUpsertRequest

logger = get_logger()


class MemoryCalculator(BaseModel):
    conversation_history_request: ConversationHistoryRequest
    conversation_history: ConversationHistory
    limit_messages: int = None
    memory: ChatbotConversationMemory = ChatbotConversationMemory()

    @classmethod
    async def from_conversation_history_request(cls, conversation_history_request: ConversationHistoryRequest,
                                                **kwargs):
        conversation_history = await get_conversation_history(conversation_history_request=conversation_history_request)
        return cls(conversation_history_request=conversation_history_request,
                   conversation_history=conversation_history,
                   **kwargs)

    @classmethod
    async def from_chat_request(cls,
                                chat_request: ChatRequest,

                                **kwargs):
        conversation_history_request = ConversationHistoryRequest.from_chat_request(chat_request=chat_request)
        return await cls.from_conversation_history_request(
            conversation_history_request=conversation_history_request,
            **kwargs)

    async def calculate(self, upsert: bool = True):
        self.load_memory_from_history(conversation_history=self.conversation_history)
        conversation_memory_document = ConversationMemoryDocument(
            context_route=self.conversation_history_request.context_route,
            buffer=self.memory.buffer,
            summary=self.memory.moving_summary_buffer,
            summary_prompt=self.memory.prompt,
            )

        await conversation_memory_document.save(database_name=self.conversation_history_request.database_name,
                                                collection_name=self.conversation_history_request.memories_collection_name)


    def load_memory_from_history(self,
                                 conversation_history=ConversationHistory,
                                 max_tokens=CONVERSATION_HISTORY_MAX_TOKENS,
                                 limit_messages=None):
        logger.info(
            f"Loading {len(conversation_history.get_all_messages())} messages into memory (class: {self.memory.__class__}).")

        message_count = -1
        for chat_message in conversation_history.get_all_messages():
            message_count += 1
            if limit_messages is not None:
                if message_count > limit_messages:
                    break
            if chat_message.speaker.type == "human":
                human_message = f"On {str(chat_message.timestamp)} the human `{chat_message.speaker.name}` said: {chat_message.message}"
                logger.trace(f"Adding human message: {human_message}")
                self.memory.chat_memory.add_user_message(human_message)
            elif chat_message.speaker.type == "bot":
                ai_message = f"On {str(chat_message.timestamp)}, the AI (you) `{chat_message.speaker.name}` said: {chat_message.message}"
                logger.trace(f"Adding AI message: {ai_message}")
                self.memory.chat_memory.add_ai_message(ai_message)
            memory_token_length = self.memory.llm.get_num_tokens_from_messages(
                messages=self.memory.chat_memory.messages)
            if memory_token_length > max_tokens:
                logger.info(f"Memory token length {memory_token_length} exceeds max tokens {max_tokens}. Pruning...")
                logger.info(f"Memory summary before pruning: {self.memory.moving_summary_buffer}\n---\n")
                self.memory.prune()
                logger.info(f"Memory summary after pruning: {self.memory.moving_summary_buffer}")


async def calculate_memory(chat_request: ChatRequest):
    memory_calculator = await MemoryCalculator.from_chat_request(chat_request=chat_request)
    memory = await memory_calculator.calculate(upsert=True)
    return memory


class ConversationMemoryDocument(BaseModel):
    context_route: ContextRoute
    buffer: List[BaseMessage] = []
    summary: str = ""
    summary_prompt: PromptTemplate

    async def save(self,
                   database_name: str,
                   collection_name: str):
        await database_upsert(DatabaseUpsertRequest(query=self.context_route,
                                                    database_name=database_name,
                                                    collection_name=collection_name,
                                                    data=self.dict()))


if __name__ == "__main__":
    from jonbot.tests.load_save_sample_data import load_sample_chat_request

    chat_request = load_sample_chat_request()
    chat_request.config.limit_messages = None
    asyncio.run(calculate_memory(chat_request=chat_request))


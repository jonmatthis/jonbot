import asyncio

from pydantic import BaseModel

from jonbot import get_logger
from jonbot.layer2_core_processes.core.ai.components.memory.sub_memory_components.conversation_memory import \
    ChatbotConversationMemory
from jonbot.layer2_core_processes.entrypoint_functions.database_actions import get_message_history_document, \
    database_upsert
from jonbot.models.context_memory_document import ContextMemoryDocument
from jonbot.models.context_route import ContextRoute
from jonbot.models.conversation_models import ChatRequest, MessageHistory
from jonbot.models.database_request_response_models import MessageHistoryRequest, DatabaseUpsertRequest
from jonbot.models.memory_config import CONVERSATION_HISTORY_MAX_TOKENS
from jonbot.models.timestamp_model import Timestamp

logger = get_logger()


class ConversationMemoryCalculator(BaseModel):
    message_history_request: MessageHistoryRequest
    message_history: MessageHistory
    limit_messages: int = None
    memory: ChatbotConversationMemory = ChatbotConversationMemory()

    @classmethod
    async def from_message_history_request(cls, message_history_request: MessageHistoryRequest,
                                                **kwargs):
        message_history = await get_message_history_document(message_history_request=message_history_request)
        if message_history is None:
            logger.warning(f"Message history not found for request: {message_history_request.dict()}")
            return

        return cls(message_history_request=message_history_request,
                   message_history=message_history,
                   **kwargs)

    @classmethod
    async def from_chat_request(cls,
                                chat_request: ChatRequest,

                                **kwargs):
        message_history_request = MessageHistoryRequest.from_chat_request(chat_request=chat_request)
        return await cls.from_message_history_request(
            message_history_request=message_history_request,
            **kwargs)

    @classmethod
    async def from_context_route(cls,
                                 context_route: ContextRoute,
                                 database_name: str,
                                 limit_messages: int = None,
                                 **kwargs):
        message_history_request = MessageHistoryRequest(database_name=database_name,
                                                             context_route=context_route,
                                                             limit_messages=limit_messages)
        return await cls.from_message_history_request(
            message_history_request=message_history_request,
            **kwargs)

    async def calculate(self, upsert: bool = True):
        self.construct_memory_from_history(message_history=self.message_history)
        context_memory_document = ContextMemoryDocument(
            context_route=self.message_history_request.context_route,
            buffer=self.memory.buffer,
            summary=self.memory.moving_summary_buffer,
            summary_prompt=self.memory.prompt,
        )

        if upsert:
            await self.upsert_memory(database_name=self.message_history_request.database_name,
                                     context_memory_document=context_memory_document)

    async def upsert_memory(self,
                            context_memory_document: ContextMemoryDocument,
                            database_name: str):
        await database_upsert(DatabaseUpsertRequest(query=context_memory_document.context_route.as_query,
                                                    database_name=database_name,
                                                    collection_name=context_memory_document.context_memories_collection_name,
                                                    data={"last_updated": Timestamp.now(),
                                                          **self.dict()}
                                                    )
                              )

    def construct_memory_from_history(self,
                                      message_history=MessageHistory,
                                      max_tokens=CONVERSATION_HISTORY_MAX_TOKENS,
                                      limit_messages=None):
        logger.info(
            f"Loading {len(message_history.get_all_messages())} messages into memory (class: {self.memory.__class__}).")

        message_count = -1
        for chat_message in message_history.get_all_messages():
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


async def calculate_memory_from_chat_request(chat_request: ChatRequest):
    memory_calculator = await ConversationMemoryCalculator.from_chat_request(chat_request=chat_request)
    memory = await memory_calculator.calculate(upsert=True)
    return memory


async def calculate_memory_from_context_route(context_route: ContextRoute,
                                              database_name: str,
                                              limit_messages: int = None):
    try:
        memory_calculator = await ConversationMemoryCalculator.from_context_route(context_route=context_route,
                                                                                  database_name=database_name,
                                                                                  limit_messages=limit_messages)
        if memory_calculator is None:
            logger.warning(f"`MemoryCalculator` returned  `None` for context route: {context_route}")
            return False
        else:
            memory = await memory_calculator.calculate(upsert=True)
    except Exception as e:
        logger.error(f"Error occurred while calculating memory from context route: {context_route}. Error: {e}")
        raise

    return True


if __name__ == "__main__":
    from jonbot.tests.load_save_sample_data import load_sample_chat_request

    chat_request = load_sample_chat_request()
    chat_request.config.limit_messages = None
    asyncio.run(calculate_memory_from_chat_request(chat_request=chat_request))

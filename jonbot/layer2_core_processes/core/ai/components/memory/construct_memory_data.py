import asyncio

from langchain.schema import HumanMessage, AIMessage
from pydantic import BaseModel

from jonbot import get_logger
from jonbot.layer2_core_processes.core.ai.components.memory.conversation_memory.conversation_memory import \
    ChatbotConversationMemory
from jonbot.layer2_core_processes.entrypoint_functions.backend_database_actions import get_message_history_document, \
    update_context_memory, get_context_memory_document
from jonbot.models.context_memory_document import ContextMemoryDocument
from jonbot.models.context_route import ContextRoute
from jonbot.models.conversation_models import ChatRequest, MessageHistory
from jonbot.models.database_request_response_models import MessageHistoryRequest, UpdateContextMemoryRequest
from jonbot.models.memory_config import CONVERSATION_HISTORY_MAX_TOKENS

logger = get_logger()


class ConversationMemoryCalculator(BaseModel):
    message_history_request: MessageHistoryRequest
    current_context_memory: ContextMemoryDocument = None
    message_history: MessageHistory
    limit_messages: int = None
    memory: ChatbotConversationMemory = ChatbotConversationMemory()

    @classmethod
    async def from_message_history_request(cls, message_history_request: MessageHistoryRequest,
                                           **kwargs):
        current_context_memory = await get_context_memory_document(context_route=message_history_request.context_route,
                                                                     database_name=message_history_request.database_name)
        message_history = await get_message_history_document(message_history_request=message_history_request)
        if message_history is None:
            logger.warning(f"Message history not found for request: {message_history_request.dict()}")
            return

        for message in message_history.get_all_messages():
            logger.trace(f"Message: {message}")


        return cls(message_history_request=message_history_request,
                   current_context_memory=current_context_memory,
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

    async def calculate(self, upsert: bool = True) -> ContextMemoryDocument:

        self.construct_memory_from_history(message_history=self.message_history)

        context_memory_document = ContextMemoryDocument(
            context_route=self.message_history_request.context_route,
            message_buffer=[message.dict() for message in self.memory.buffer],
            summary=self.memory.moving_summary_buffer,
            summary_prompt=self.memory.prompt,
        )

        if upsert:
            await self.upsert_memory(database_name=self.message_history_request.database_name,
                                     context_memory_document=context_memory_document)

        return context_memory_document

    async def upsert_memory(self,
                            context_memory_document: ContextMemoryDocument,
                            database_name: str):

        await update_context_memory(UpdateContextMemoryRequest(context_memory_document=context_memory_document,
                                                               database_name=database_name,
                                                               context_route=context_memory_document.context_route))

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
                human_message = HumanMessage(
                    content=f"{chat_message.message} [metadata - 'username':{chat_message.speaker.name},'local_time': {chat_message.timestamp.human_readable_local}]",
                    additional_kwargs={**chat_message.dict(),
                                       "type": "human"})

                logger.trace(f"Adding human message: {human_message}")
                self.memory.chat_memory.add_message(human_message)
            elif chat_message.speaker.type == "bot":
                ai_message = AIMessage(
                    content=f"{chat_message.message} - [metadata - 'username':{chat_message.speaker.name},'local_time': {chat_message.timestamp.human_readable_local}, 'notes': (this is you)]",
                    additional_kwargs={**chat_message.dict(),
                                       "type": "ai"})
                logger.trace(f"Adding AI message: {ai_message}")
                self.memory.chat_memory.add_message(ai_message)
            memory_token_length = self.memory.llm.get_num_tokens_from_messages(
                messages=self.memory.chat_memory.messages)
            if memory_token_length > max_tokens:
                logger.info(f"Memory token length {memory_token_length} exceeds max tokens {max_tokens}. Pruning...")
                logger.info(f"Memory summary before pruning: {self.memory.moving_summary_buffer}\n---\n")
                self.memory.prune()
                logger.info(f"Memory summary after pruning: {self.memory.moving_summary_buffer}")

        self.memory.moving_summary_buffer = self.memory.predict_new_summary(messages=self.memory.chat_memory.messages,
                                                                            existing_summary=self.memory.moving_summary_buffer)


async def calculate_memory_from_chat_request(chat_request: ChatRequest):
    memory_calculator = await ConversationMemoryCalculator.from_chat_request(chat_request=chat_request)
    memory = await memory_calculator.calculate(upsert=True)
    return memory


async def calculate_memory_from_context_route(context_route: ContextRoute,
                                              database_name: str,
                                              limit_messages: int = None) -> ContextMemoryDocument:
    try:
        memory_calculator = await ConversationMemoryCalculator.from_context_route(context_route=context_route,
                                                                                  database_name=database_name,
                                                                                  limit_messages=limit_messages)
        if memory_calculator is None:
            logger.exception(f"`MemoryCalculator` returned  `None` for context route: {context_route}")
            return
        else:
            context_memory_document = await memory_calculator.calculate(upsert=True)
    except Exception as e:
        logger.error(f"Error occurred while calculating memory from context route: {context_route}. Error: {e}")
        raise

    return context_memory_document


if __name__ == "__main__":
    from jonbot.tests.load_save_sample_data import load_sample_chat_request

    chat_request = load_sample_chat_request()
    chat_request.config.limit_messages = None
    asyncio.run(calculate_memory_from_chat_request(chat_request=chat_request))

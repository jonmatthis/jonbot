import asyncio
from typing import AsyncIterable, Any, Dict

import langchain
from langchain.chat_models import ChatOpenAI
from langchain.schema.runnable import RunnableMap, RunnableSequence

from jonbot import get_logger
from jonbot.layer0_frontends.discord_bot.handlers.handle_message_responses import STOP_STREAMING_TOKEN
from jonbot.layer2_processing.controller.entrypoint_functions.backend_database_operations import \
    BackendDatabaseOperations
from jonbot.layer2_processing.core_processing.ai.components.memory.conversation_memory.conversation_memory import \
    ChatbotConversationMemory
from jonbot.layer2_processing.core_processing.ai.components.prompt.prompt_builder import ChatbotPrompt
from jonbot.models.context_memory_document import ContextMemoryDocument
from jonbot.models.context_route import ContextRoute
from jonbot.models.database_request_response_models import UpsertContextMemoryRequest

langchain.debug = True

logger = get_logger()


class ChatbotLLMChain:
    context_memory_document: ContextMemoryDocument = None

    def __init__(self,
                 context_route: ContextRoute,
                 database_name: str,
                 database_operations: BackendDatabaseOperations,
                 chat_history_placeholder_name: str = "chat_history"):
        self.context_route = context_route
        self.database_name = database_name
        self.database_operations = database_operations
        self.model = ChatOpenAI(temperature=0.8,
                                model_name="gpt-4",
                                verbose=True,
                                )
        self.prompt = ChatbotPrompt.build(chat_history_placeholder_name=chat_history_placeholder_name)

        self.memory = ChatbotConversationMemory()
        self.chain = self._build_chain()

    @classmethod
    async def from_context_route(cls,
                                 context_route: ContextRoute,
                                 database_name: str,
                                 database_operations: BackendDatabaseOperations):
        instance = cls(context_route=context_route,
                       database_name=database_name,
                       database_operations=database_operations)

        await instance.load_context_memory()
        return instance

    def _build_chain(self) -> RunnableSequence:
        return RunnableMap({
            "human_input": lambda x: x["human_input"],
            "memory": self.memory.load_memory_variables,
        }) | {
            "human_input": lambda x: x["human_input"],
            "chat_history": lambda x: x["memory"]["chat_memory"]
        } | self.prompt | self.model

    async def execute(self, message_string: str, pause_at_end: float = 1.0) -> AsyncIterable[str]:
        inputs = {"human_input": message_string}
        response_message = ""
        try:
            async for token in self.chain.astream(inputs):
                logger.trace(f"Yielding token: {repr(token.content)}")
                response_message += token.content
                yield token.content
            yield STOP_STREAMING_TOKEN

            await asyncio.sleep(pause_at_end)  # give it a sec to clear the buffer

            logger.debug(f"Successfully executed chain! - Saving context to memory...")
            self._update_memory(inputs=inputs,
                                outputs={"output": response_message})
            await self.upsert_context_memory()
            logger.trace(f"Response message: {response_message}")
        except Exception as e:
            logger.exception(e)
            raise

    async def load_context_memory(self):
        self.context_memory_document = await self.database_operations.get_context_memory_document(
            database_name=self.database_name,
            context_route=self.context_route)
        if self.context_memory_document is None:
            logger.warning(
                f"Could not load context memory from database for context route: {self.context_route.dict()}")
        else:
            self.memory.load_context_memory(context_memory_document=self.context_memory_document)

    async def upsert_context_memory(self):
        logger.debug(f"Upserting context memory for context route: {self.context_route.dict()}")
        if self.context_memory_document is not None:
            try:
                await self.database_operations.upsert_context_memory(
                    UpsertContextMemoryRequest(database_name=self.database_name,
                                               data=self.context_memory_document,
                                               query=self.context_route.as_query, ))
            except Exception as e:
                logger.exception(e)
                raise

    def _update_memory(self, inputs: Dict[str, Any], outputs: Dict[str, Any]):
        self.memory.save_context(inputs=inputs,
                                 outputs=outputs)

        self.context_memory_document = ContextMemoryDocument(context_route=self.context_route,
                                                             message_buffer=[message.dict() for message in
                                                                             self.memory.buffer],
                                                             summary=self.memory.moving_summary_buffer,
                                                             summary_prompt=self.memory.prompt,
                                                             )


async def demo():
    from jonbot.tests.load_save_sample_data import load_sample_message_history

    conversation_history = await load_sample_message_history()
    llm_chain = ChatbotLLMChain(conversation_history=conversation_history)
    async for token in llm_chain.chain.astream({"human_input": "Hello, how are you?"}):  # Use 'async for' here
        print(token.content)
    f = 9


if __name__ == "__main__":
    asyncio.run(demo())

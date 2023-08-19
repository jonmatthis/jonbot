import asyncio
from typing import AsyncIterable

import langchain
from langchain.chat_models import ChatOpenAI
from langchain.schema.runnable import RunnableMap, RunnableSequence

from jonbot import get_logger
from jonbot.layer0_frontends.discord_bot.handlers.handle_message_responses import STOP_STREAMING_TOKEN
from jonbot.layer2_core_processes.core.ai.components.memory.conversation_memory.conversation_memory import \
    ChatbotConversationMemory
from jonbot.layer2_core_processes.core.ai.components.prompt.prompt_builder import ChatbotPrompt
from jonbot.layer2_core_processes.entrypoint_functions.backend_database_actions import get_context_memory_document
from jonbot.models.context_route import ContextRoute
from jonbot.models.conversation_models import MessageHistory

langchain.debug = True

logger = get_logger()


class ChatbotLLMChain:
    def __init__(self,
                 conversation_history: MessageHistory = None,
                 chat_history_placeholder_name: str = "chat_history"):
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
                                 database_name: str):
        instance = cls()
        await instance.load_context_memory(context_route=context_route,
                                           database_name=database_name)
        return instance

    def _build_chain(self) -> RunnableSequence:
        return RunnableMap({
            "human_input": lambda x: x["human_input"],
            "memory": self.memory.load_memory_variables,
        }) | {
            "human_input": lambda x: x["human_input"],
            "chat_history": lambda x: x["memory"]["chat_memory"]
        } | self.prompt | self.model

    async def execute(self, message_string: str, pause_at_end:float=1.0 ) -> AsyncIterable[str]:
        inputs = {"human_input": message_string}
        response_message = ""
        try:
            async for token in self.chain.astream(inputs):
                logger.trace(f"Yielding token: {repr(token.content)}")
                response_message += token.content
                yield token.content
            yield STOP_STREAMING_TOKEN

            await asyncio.sleep(pause_at_end) # give it a sec to clear the buffer

            logger.debug(f"Successfully executed chain! - Saving context to memory...")
            self.memory.save_context(inputs, {"output": response_message})
            logger.trace(f"Response message: {response_message}")
        except Exception as e:
            logger.exception(e)
            raise



    async def load_context_memory(self,
                                  context_route: ContextRoute,
                                  database_name:str):
        context_memory_document = await get_context_memory_document(context_route=context_route,
                                                                    database_name=database_name)
        if context_memory_document is None:
            logger.warning(f"Could not load context memory from database for context route: {context_route.dict()}")
        else:
            self.memory.load_context_memory(context_memory_document=context_memory_document)


async def demo():
    from jonbot.tests.load_save_sample_data import load_sample_message_history

    conversation_history = await load_sample_message_history()
    llm_chain = ChatbotLLMChain(conversation_history=conversation_history)
    async for token in llm_chain.chain.astream({"human_input": "Hello, how are you?"}):  # Use 'async for' here
        print(token.content)
    f = 9


if __name__ == "__main__":
    asyncio.run(demo())

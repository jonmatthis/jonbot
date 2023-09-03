import asyncio
from typing import AsyncIterable

from langchain.chat_models import ChatOpenAI, ChatAnthropic
from langchain.schema.runnable import RunnableMap, RunnableSequence

from jonbot import get_jonbot_logger
from jonbot.layer0_frontends.discord_bot.handlers.discord_message_responder import (
    STOP_STREAMING_TOKEN,
)
from jonbot.layer2_processing.ai.chatbot.components.memory.conversation_memory.conversation_memory import (
    ChatbotConversationMemory,
)
from jonbot.layer2_processing.ai.chatbot.components.prompt.prompt_builder import (
    ChatbotPrompt,
)
from jonbot.layer2_processing.backend_database_operator.backend_database_operator import (
    BackendDatabaseOperations,
)
from jonbot.models.context_route import ContextRoute

# langchain.debug = True

logger = get_jonbot_logger()


class ChatbotLLMChain:
    def __init__(
            self,
            context_route: ContextRoute,
            database_name: str,
            database_operations: BackendDatabaseOperations,
            chat_history_placeholder_name: str = "chat_history",
    ):
        self.llm_main = ChatOpenAI(
            temperature=0.8,
            model_name="gpt-4",
            verbose=True,
        )
        self.llm_backup = ChatOpenAI(
            temperature=0.8,
            model_name="gpt-3.5-turbo-16k",
            verbose=True,
        )
        self.llm_backup_backup = ChatAnthropic(
            temperature=0.8,
            model="claude-2",
            verbose=True,
        )
        self.llm = self.llm_main.with_fallbacks([self.llm_backup, self.llm_backup_backup])

        self.prompt = ChatbotPrompt.build(
            chat_history_placeholder_name=chat_history_placeholder_name
        )

        self.memory = ChatbotConversationMemory(
            database_operations=database_operations,
            database_name=database_name,
            context_route=context_route,
        )
        self.chain = self._build_chain()

    @classmethod
    async def from_context_route(
            cls,
            context_route: ContextRoute,
            database_name: str,
            database_operations: BackendDatabaseOperations,
    ):
        instance = cls(
            context_route=context_route,
            database_name=database_name,
            database_operations=database_operations,
        )

        await instance.memory.configure_memory()
        return instance

    def _build_chain(self) -> RunnableSequence:
        return (
                RunnableMap(
                    {
                        "human_input": lambda x: x["human_input"],
                        "memory": self.memory.load_memory_variables,
                    }
                )
                | {
                    "human_input": lambda x: x["human_input"],
                    "chat_history": lambda x: x["memory"]["chat_memory"],
                }
                | self.prompt
                | self.llm
        )

    async def execute(
            self, message_string: str, pause_at_end: float = 1.0
    ) -> AsyncIterable[str]:
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

            await self.memory.update(
                inputs=inputs, outputs={"output": response_message}
            )

            logger.trace(f"Response message: {response_message}")
        except Exception as e:
            logger.exception(e)
            raise


async def demo():
    from jonbot.tests.load_save_sample_data import load_sample_message_history

    conversation_history = await load_sample_message_history()
    llm_chain = ChatbotLLMChain(conversation_history=conversation_history)
    async for token in llm_chain.chain.astream(
            {"human_input": "Hello, how are you?"}
    ):  # Use 'async for' here
        print(token.content)
    f = 9


if __name__ == "__main__":
    asyncio.run(demo())

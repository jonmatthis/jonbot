from typing import AsyncIterable

from langchain.chat_models import ChatOpenAI
from langchain.schema.runnable import RunnableMap, RunnableSequence

from jonbot import get_logger
from jonbot.layer0_frontends.discord_bot.handlers.discord_message_responder import (
    STOP_STREAMING_TOKEN,
)
from jonbot.layer2_processing.ai.chatbot.components.memory.conversation_memory.conversation_memory import (
    ChatbotConversationMemory,
)
from jonbot.layer2_processing.ai.chatbot.components.memory.memory_handler import (
    MemoryHandler,
)
from jonbot.layer2_processing.ai.chatbot.components.prompt.prompt_builder import (
    ChatbotPrompt,
)

# langchain.debug = True

logger = get_logger()


class Chatbot:
    def __init__(
        self,
        memory_handler: MemoryHandler,
        chat_history_placeholder_name: str = "chat_history",
    ):
        self.model = ChatOpenAI(
            temperature=0.8,
            model_name="gpt-4",
            verbose=True,
        )
        self.prompt = ChatbotPrompt.build(
            chat_history_placeholder_name=chat_history_placeholder_name
        )

        self.memory = ChatbotConversationMemory(
            memory_handler=memory_handler,
        )
        self.chain = self._build_chain()

    @classmethod
    async def from_memory_handler(
        cls,
        memory_handler: MemoryHandler,
    ):
        instance = cls(
            memory_handler=memory_handler,
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
            | self.model
        )

    async def execute(self, message_string: str) -> AsyncIterable[str]:
        inputs = {"human_input": message_string}
        response_message = ""
        try:
            async for token in self.chain.astream(inputs):
                logger.trace(f"Yielding token: {repr(token.content)}")
                response_message += token.content
                yield token.content
            yield STOP_STREAMING_TOKEN

            logger.debug(f"Successfully executed chain! - Saving context to memory...")

            await self.memory.update(
                inputs=inputs, outputs={"output": response_message}
            )

            logger.trace(f"Response message: {response_message}")
        except Exception as e:
            logger.exception(e)
            raise


#
# async def demo():
#     from jonbot.tests.load_save_sample_data import load_sample_message_history
#
#     chat_bot = Chatbot.build_empty()
#     async for token in llm_chain.chain.astream(
#         {"human_input": "Hello, how are you?"}
#     ):  # Use 'async for' here
#         print(token.content)
#     f = 9
#
#
# if __name__ == "__main__":
#     asyncio.run(demo())

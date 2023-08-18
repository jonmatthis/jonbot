import asyncio
from typing import AsyncIterable

import langchain
from langchain.chat_models import ChatOpenAI
from langchain.schema.runnable import RunnableMap, RunnableSequence

from jonbot import get_logger
from jonbot.layer0_frontends.discord_bot.handlers.handle_message_responses import STOP_STREAMING_TOKEN
from jonbot.layer2_core_processes.core.ai.components.memory.sub_memory_components.conversation_memory import \
    ChatbotConversationMemoryBuilder
from jonbot.layer2_core_processes.core.ai.components.prompt.prompt_builder import ChatbotPrompt
from jonbot.models.conversation_models import ConversationHistory

langchain.debug = True

logger = get_logger()


class ChatbotLLMChain:
    def __init__(self,
                 conversation_history: ConversationHistory = None,
                 chat_history_placeholder_name: str = "chat_history"):
        self.model = ChatOpenAI(temperature=0.8,
                                model_name="gpt-4",
                                verbose=True,
                                )
        self.prompt = ChatbotPrompt.build(chat_history_placeholder_name=chat_history_placeholder_name)

        self.memory = ChatbotConversationMemoryBuilder.build()
        self.chain = self._build_chain()

    def _build_chain(self) -> RunnableSequence:
        return RunnableMap({
            "human_input": lambda x: x["human_input"],
            "memory": self.memory.load_memory_variables,
        }) | {
            "human_input": lambda x: x["human_input"],
            "chat_history": lambda x: x["memory"]["chat_memory"]
        } | self.prompt | self.model

    async def execute(self, message_string: str) -> AsyncIterable[str]:
        inputs = {"human_input": message_string}
        response_message = ""
        try:
            async for token in self.chain.astream(inputs):
                logger.trace(f"Yielding token: {repr(token.content)}")
                response_message += token.content
                yield token.content
            yield STOP_STREAMING_TOKEN

            logger.debug(f"Succesfully executed chain! - Saving context to memory...")
            self.memory.save_context(inputs, {"output": response_message})
            logger.trace(f"Response message: {response_message}")
        except Exception as e:
            logger.exception(e)
            raise


async def demo():
    from jonbot.tests.load_save_sample_data import load_sample_conversation_history

    conversation_history = await load_sample_conversation_history()
    llm_chain = ChatbotLLMChain(conversation_history=conversation_history)
    async for token in llm_chain.chain.astream({"human_input": "Hello, how are you?"}):  # Use 'async for' here
        print(token.content)
    f = 9



if __name__ == "__main__":
    asyncio.run(demo())

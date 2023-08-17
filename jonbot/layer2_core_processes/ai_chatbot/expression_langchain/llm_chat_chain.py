import asyncio
from typing import AsyncIterable

import langchain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema.runnable import RunnableMap, RunnableSequence

from jonbot.layer2_core_processes.ai_chatbot.components.memory.sub_memory_builders.conversation_memory_builder import \
    ChatbotConversationMemoryBuilder
from jonbot.layer2_core_processes.ai_chatbot.components.prompt.prompt_builder import ChatbotPrompt

# langchain.debug = True

from jonbot import get_logger
from jonbot.layer3_data_layer.database.get_or_create_mongo_database_manager import get_or_create_mongo_database_manager
from jonbot.models.conversation_models import ConversationHistory

logger = get_logger()



class LLMChatChain:
    def __init__(self,
                 conversation_history: ConversationHistory = None,
                 chat_history_placeholder_name:str="chat_history"):
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

    async def execute(self, message_string:str) -> AsyncIterable[str]:
        inputs = {"human_input": message_string}
        response_message = ""
        try:
            async for token in self.chain.astream(inputs):
                logger.trace(f"Yielding token: {repr(token.content)}")
                response_message += token.content
                yield token.content

            logger.debug(f"Succesfully executed chain! - Saving context to memory...")
            self.memory.save_context(inputs, {"output": response_message})
            logger.trace(f"Response message: {response_message}")
        except Exception as e:
            logger.exception(e)
            raise



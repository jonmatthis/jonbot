from typing import AsyncIterable

import langchain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.runnable import RunnableMap

from jonbot.models.conversation_models import ChatRequest

langchain.debug = True

from jonbot import get_logger
logger = get_logger()



class LLMChatChain:
    def __init__(self, message: str):
        self.message = message
        self.model = ChatOpenAI(temperature=0.8, model_name="gpt-4", verbose=True)
        self.prompt = self._create_prompt()
        self.memory = ConversationBufferMemory(return_messages=True)
        self.chain = self._build_chain()

    def _create_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("system", "You are a helpful chatbot. You are super chill and lowkey. Your personality is kind, reserved, and very casual."),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])

    def _build_chain(self) -> RunnableMap:
        return RunnableMap({
            "input": lambda x: x["input"],
            "memory": self.memory.load_memory_variables
        }) | {
            "input": lambda x: x["input"],
            "history": lambda x: x["memory"]["history"]
        } | self.prompt | self.model

    async def execute(self) -> AsyncIterable[str]:
        inputs = {"input": self.message}
        response_message = ""
        try:
            async for token in self.chain.astream(inputs):
                logger.trace(f"Sending token: {token.content}")
                response_message += token.content
                yield f"data: {token.content}\n\n"  # Use server-sent-events format to stream the response

            self.memory.save_context(inputs, {"output": response_message})
            logger.trace(f"Response message: {response_message}")
        except Exception as e:
            logger.exception(e)
            raise



import logging
from typing import AsyncIterable

from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain.schema.runnable import RunnableMap

logger = logging.getLogger(__name__)


async def chat_stream(message: str) -> AsyncIterable[str]:
    try:
        # chain = make_chain_with_expression_language()
        model = ChatOpenAI(temperature=0.8,
                           model_name="gpt-4",
                           verbose=True, )
        # prompt = ChatbotPrompt.build()
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful chatbot - you mention Chickens at every opportunity."),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])
        memory = ConversationBufferMemory(return_messages=True)
        memory.load_memory_variables({})

        chain = RunnableMap({
            "input": lambda x: x["input"],
            "memory": memory.load_memory_variables
        }) | {
                    "input": lambda x: x["input"],
                    "history": lambda x: x["memory"]["history"]
                } | prompt | model

        inputs = {"input": message}
        response_message = ""

        async for token in chain.astream(inputs):
            logger.trace(f"Sending token: {token.content}")
            response_message += token.content
            yield f"data: {token.content}\n\n"  # Use server-sent-events  format to stream the response

        memory.save_context(inputs, {"output": response_message})
        logger.trace(f"Response message: {response_message}")
    except Exception as e:
        logger.exception(e)
        raise
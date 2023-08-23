import asyncio
import sys

from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.runnable import RunnableMap


async def create_chain_with_expression_language():
    from dotenv import load_dotenv

    load_dotenv()

    callback = AsyncIteratorCallbackHandler()
    model = ChatOpenAI(
        streaming=True,
        verbose=True,
        callbacks=[callback],
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful chatbot"),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ]
    )
    memory = ConversationBufferMemory(return_messages=True)
    memory.load_memory_variables({})
    memory_input_mapping = RunnableMap(
        {"input": lambda x: x["input"], "memory": memory.load_memory_variables}
    )
    mapping = {
        "input": lambda x: x["input"],
        "history": lambda x: x["memory"]["history"],
    }
    memory_i_guess = memory_input_mapping | mapping
    chain = memory_i_guess | prompt | model
    inputs = {"input": "hi im bob"}
    response = await chain.ainvoke(inputs)
    print(f"Here that response frnd: {response}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(create_chain_with_expression_language())
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

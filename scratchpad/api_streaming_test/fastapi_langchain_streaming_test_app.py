"""This is an example of how to use async langchain with fastapi and return a streaming response.
The latest version of Langchain has improved its compatibility with asynchronous FastAPI,
making it easier to implement streaming functionality in your applications.
"""
import asyncio
import os
from typing import AsyncIterable, Awaitable

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain import LLMChain, PromptTemplate
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.chat_models import ChatOpenAI
from pydantic import BaseModel

from scratchpad.langchain_stuff.langchain_expression_language import create_chain_with_expression_language

# Two ways to load env variables
# 1.load env variables from .env file
load_dotenv()

# 2.manually set env variables
if "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] = ""

app = FastAPI()


async def send_message_expression_language(message: str) -> AsyncIterable[str]:
    chain = await create_chain_with_expression_language()

    async for token in chain.astream(inputs={"input": message}):
        # Use server-sent-events to stream the response
        print(f"Sending token: {token}")
        yield f"data: {token}\n\n"


def make_chain(callback: AsyncIteratorCallbackHandler) -> LLMChain:
    prompt_template = "Tell me a {adjective} joke"
    prompt = PromptTemplate(
        input_variables=["adjective"], template=prompt_template
    )
    llm = ChatOpenAI(
        streaming=True,
        verbose=True,
        callbacks=[callback],
    )
    return LLMChain(llm=llm, prompt=prompt)


async def send_message(message: str) -> AsyncIterable[str]:
    callback = AsyncIteratorCallbackHandler()
    chain = make_chain(callback)

    async def wrap_done(fn: Awaitable, event: asyncio.Event):
        """Wrap an awaitable with a event to signal when it's done or an exception is raised."""
        try:
            await fn
        except Exception as e:
            # TODO: handle exception
            print(f"Caught exception: {e}")
        finally:
            # Signal the aiter to stop.
            event.set()

    # Begin a task that runs in the background.
    task = asyncio.create_task(wrap_done(
        chain.agenerate(input_list=[{"adjective": "red"}]),
        callback.done),
    )

    async for token in callback.aiter():
        # Use server-sent-events to stream the response
        print(f"Sending token: {token}")
        yield f"data: {token}\n\n"

    await task


class StreamRequest(BaseModel):
    """Request body for streaming."""
    message: str


@app.post("/stream")
def stream(body: StreamRequest):
    return StreamingResponse(send_message(body.message), media_type="text/event-stream")


if __name__ == "__main__":
    uvicorn.run(host="localhost", port=8000, app=app)

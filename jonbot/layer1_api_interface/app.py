import asyncio
import logging
import time

from fastapi import FastAPI

from jonbot.layer2_core_processes.controller.controller import Controller
from jonbot.layer3_data_layer.data_models.conversation_models import ChatInput, ChatResponse

logger = logging.getLogger(__name__)

API_CHAT_URL = "http://localhost:8000/chat"

app = FastAPI()
controller = asyncio.run(Controller.initialize())


@app.post("/chat")
async def chat(chat_input: ChatInput) -> ChatResponse:
    """
    Process the chat input
    """
    logger.info(f"Received chat input: {chat_input}")
    tic = time.perf_counter()
    response = await controller.handle_chat_input(chat_input=chat_input)
    toc = time.perf_counter()
    logger.info(f"Returning chat response: {response}, elapsed time: {toc - tic:0.4f} seconds")
    return response


def run_api():
    """
    Run the API for JonBot
    """
    logger.info("Starting API")
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)

if __name__ == '__main__':
    run_api()

import asyncio
import logging
import os
import time
import uuid
import aiofiles
import aiohttp
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

from jonbot.layer2_core_processes.controller.controller import Controller
from jonbot.layer2_core_processes.processing_sublayer.audio_transcription.transcribe_audio import transcribe_audio
from jonbot.layer3_data_layer.data_models.conversation_models import ChatInput, ChatResponse

logger = logging.getLogger(__name__)

API_CHAT_URL = "http://localhost:8000/chat"
API_VOICE_TO_TEXT_URL = "http://localhost:8000/voice_to_text"

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

class VoiceToTextRequest(BaseModel):
    audio_file_url: str
    prompt: str = None
    response_format: str = None
    temperature: float = None
    language: str = None

@app.post("/voice_to_text")
async def voice_to_text(request: VoiceToTextRequest) -> ChatResponse:
    transcript_text = await transcribe_audio(
        request.audio_file_url,
        prompt=request.prompt,
        response_format=request.response_format,
        temperature=request.temperature,
        language=request.language
    )
    return ChatResponse(message=transcript_text)
def run_api():
    """
    Run the API for JonBot
    """
    logger.info("Starting API")
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)


if __name__ == '__main__':
    run_api()

import asyncio
import logging
import time
from fastapi import FastAPI


from jonbot.layer2_core_processes.ai_chatbot.ai_chatbot import AIChatBot
from jonbot.layer2_core_processes.audio_transcription.transcribe_audio import transcribe_audio
from jonbot.layer3_data_layer.data_models.conversation_models import ChatInput, ChatResponse
from jonbot.layer3_data_layer.data_models.voice_to_text_request import VoiceToTextRequest, VoiceToTextResponse

logger = logging.getLogger(__name__)

API_CHAT_URL = "http://localhost:8000/chat"
API_VOICE_TO_TEXT_URL = "http://localhost:8000/voice_to_text"
API_CHAT_STREAM_URL = "http://localhost:8000/chat_stream"

app = FastAPI()



# @app.post("/chat_stream")
# async def chat_stream(chat_input: ChatInput):
#     """
#     Stream the chat response
#     """
#     logger.info(f"Received chat input: {chat_input}")
#
#     stream_handler = StreamMessageHandler(controller=controller, chat_input=chat_input)
#     generator = stream_handler.generate_messages()
#
#     return StreamingResponse(generator, media_type="text/plain")


@app.post("/chat")
async def chat(chat_input: ChatInput) -> ChatResponse:
    """
    Process the chat input
    """
    logger.info(f"Received chat input: {chat_input}")
    tic = time.perf_counter()
    bot = await AIChatBot().create_chatbot()
    response_text = await bot.async_process_human_input_text(input_text=chat_input.message)
    chat_response = ChatResponse(message=response_text)
    toc = time.perf_counter()
    logger.info(f"Returning chat response: {chat_response}, elapsed time: {toc - tic:0.4f} seconds")
    return chat_response


@app.post("/voice_to_text")
async def voice_to_text(request: VoiceToTextRequest) -> VoiceToTextResponse:
    transcript_text = await transcribe_audio(
        request.audio_file_url,
        prompt=request.prompt,
        response_format=request.response_format,
        temperature=request.temperature,
        language=request.language
    )
    return VoiceToTextResponse(text=transcript_text)


def run_api():
    """
    Run the API for JonBot
    """
    logger.info("Starting API")
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)


if __name__ == '__main__':
    run_api()

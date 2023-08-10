import asyncio
import logging

from fastapi import FastAPI
from langchain.callbacks.base import AsyncCallbackHandler
from starlette.responses import StreamingResponse
from uvicorn import Config, Server

from jonbot.layer2_core_processes.ai_chatbot.ai_chatbot import AIChatBot
from jonbot.layer2_core_processes.audio_transcription.transcribe_audio import transcribe_audio
from jonbot.layer3_data_layer.data_models.conversation_models import ChatResponse, ChatRequest
from jonbot.layer3_data_layer.data_models.database_upsert_models import DatabaseUpsertResponse, DatabaseUpsertRequest
from jonbot.layer3_data_layer.data_models.voice_to_text_request import VoiceToTextRequest, VoiceToTextResponse
from jonbot.layer3_data_layer.database.get_or_create_mongo_database_manager import get_or_create_mongo_database_manager

logger = logging.getLogger(__name__)

CHAT_ENDPOINT = "/chat"
VOICE_TO_TEXT_ENDPOINT = "/voice_to_text"
CHAT_STREAM_ENDPOINT = "/chat_stream"
DATABASE_UPSERT_ENDPOINT = "/database_upsert"

STREAMING_RESPONSE_TEST_ENDPOINT = "/test_streaming_response"

API_CHAT_URL = f"http://localhost:8000{CHAT_ENDPOINT}"
API_VOICE_TO_TEXT_URL = f"http://localhost:8000{VOICE_TO_TEXT_ENDPOINT}"
API_CHAT_STREAM_URL = f"http://localhost:8000{CHAT_STREAM_ENDPOINT}"
API_DATABASE_UPSERT_URL = f"http://localhost:8000{DATABASE_UPSERT_ENDPOINT}"

API_STREAMING_RESPONSE_TEST_URL = f"http://localhost:8000{STREAMING_RESPONSE_TEST_ENDPOINT}"
app = FastAPI()


@app.on_event("startup")
async def startup_event():
    await get_or_create_mongo_database_manager()


@app.post(CHAT_ENDPOINT, response_model=ChatResponse)
async def chat(chat_request: ChatRequest) -> ChatResponse:
    logger.info(f"Received chat request: {chat_request}")

    mongo_database = await get_or_create_mongo_database_manager()
    conversation_history = await mongo_database.get_conversation_history(
        context_route=chat_request.conversation_context.context_route)

    ai_chat_bot = await AIChatBot.create(conversation_context=chat_request.conversation_context,
                                         conversation_history=conversation_history, )

    chat_response = await ai_chat_bot.get_chat_response(chat_input_string=chat_request.chat_input.message)

    return chat_response


class PutTokenInQueueHandler(AsyncCallbackHandler):
    def __init__(self, queue: asyncio.Queue):
        super().__init__()
        self.queue = queue

    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        print(f"PutTokenInQueueHandler: {token}")
        self.queue.put_nowait(token)


class StreamingResponseHandler:
    def __init__(self,
                 ai_chat_bot: AIChatBot,
                 queue: asyncio.Queue,
                 input_message_text: str):
        self.ai_chat_bot = ai_chat_bot
        self.queue = queue
        self.input_message_text = input_message_text

    async def get_response(self):
        logger.info("Starting `get_response` task")
        await self.ai_chat_bot.get_chat_response(chat_input_string=self.input_message,
                                                 return_response=False)

    async def process_tokens(self):
        logger.info("Starting `process_tokens` task")
        while True:
            token = await self.queue.get()
            print(f"grabbed token from queue: {token}")
            if token is None:  # signal to stop streaming
                break
            yield token
            self.queue.task_done()

    async def run(self):
        logger.info("Running `StreamingResponseHandler`")
        response_task = asyncio.create_task(self.get_response())

        async for token in self.process_tokens():
            print(f"yielding token: {token}")
            yield token

        await response_task


@app.post(CHAT_STREAM_ENDPOINT, response_class=StreamingResponse)
async def chat_stream(chat_request: ChatRequest):
    logger.info(f"Received chat_stream request: {chat_request}")

    mongo_database = await get_or_create_mongo_database_manager()
    conversation_history = await mongo_database.get_conversation_history(
        context_route=chat_request.conversation_context.context_route)

    ai_chat_bot = await AIChatBot.create(conversation_context=chat_request.conversation_context,
                                         conversation_history=conversation_history, )

    queue = asyncio.Queue()
    ai_chat_bot.add_callback_handler(handler=PutTokenInQueueHandler(queue=queue))

    stream_response_handler = StreamingResponseHandler(ai_chat_bot=ai_chat_bot,
                                                       queue=queue,
                                                       input_message_text=chat_request.chat_input.message)

    async def stream_response():
        async for token in stream_response_handler.run():
            yield token

    return StreamingResponse(stream_response(), media_type="text/plain")


@app.post(STREAMING_RESPONSE_TEST_ENDPOINT)
async def streaming_response_test():
    async def generate():
        for chunk in range(10):
            yield f"Data {chunk}\n"
            await asyncio.sleep(1)  # simulate some delay

    return StreamingResponse(generate(), media_type="text/plain")


@app.post(VOICE_TO_TEXT_ENDPOINT, response_model=VoiceToTextResponse)
async def voice_to_text(request: VoiceToTextRequest) -> VoiceToTextResponse:
    transcript_text = await transcribe_audio(
        request.audio_file_url,
        prompt=request.prompt,
        response_format=request.response_format,
        temperature=request.temperature,
        language=request.language
    )
    return VoiceToTextResponse(text=transcript_text)


@app.post(DATABASE_UPSERT_ENDPOINT, response_model=DatabaseUpsertResponse)
async def database_upsert(database_upsert_request: DatabaseUpsertRequest) -> DatabaseUpsertResponse:
    logger.info(f"Upserting data into database query - {database_upsert_request.query}")
    mongo_database = await get_or_create_mongo_database_manager()
    success = await mongo_database.upsert(**database_upsert_request.dict())
    if success:
        return DatabaseUpsertResponse(success=True)
    else:
        return DatabaseUpsertResponse(success=False)


def run_api():
    """
    Run the API for JonBot
    """
    logger.info("Starting API")
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)


async def run_api_async():
    """
    Run the API for JonBot
    """
    logger.info("Starting API")
    config = Config(app=app, host="localhost", port=8000)
    server = Server(config)
    await server.serve()


def run_api_sync():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_api_async())


if __name__ == '__main__':
    asyncio.run(run_api_async())

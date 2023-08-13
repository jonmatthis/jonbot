import gradio as gr
from jonbot.layer1_api_interface.api_client.api_client import ApiClient
from jonbot.layer1_api_interface.routes import CHAT_ENDPOINT, HEALTH_ENDPOINT
from jonbot.models.conversation_models import ChatRequest
from jonbot.models.timestamp_model import Timestamp
import asyncio

api_client = ApiClient()

async def check_health():
    response = await api_client.send_request_to_api(HEALTH_ENDPOINT, type="GET")
    return response.get("status") == "alive"

async def communicate_with_api(user_message: str):
    response = await api_client.send_request_to_api(CHAT_ENDPOINT, data=ChatRequest.from_text(user_message,
                                                                                              timestamp=Timestamp.now()).dict())
    return response.get("response", "Sorry, I could not get a response from the server.")

def user(user_message, history):
    loop = asyncio.get_event_loop()
    response_message = loop.run_until_complete(communicate_with_api(user_message))
    return "", history + [[user_message, response_message]]

with gr.Blocks() as demo:
    chatbot = gr.Chatbot()
    message_textbox = gr.Textbox()
    clear = gr.Button("Clear")

    message_textbox.submit(user, [message_textbox, chatbot], [message_textbox, chatbot], queue=False)
    clear.click(lambda: None, None, chatbot, queue=False)

demo.queue()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    health_check = loop.run_until_complete(check_health())
    if health_check:
        print("Connected to API successfully!")
        demo.launch()
    else:
        print("Failed to connect to API!")

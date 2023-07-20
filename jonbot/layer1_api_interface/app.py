
from fastapi import FastAPI


from jonbot.layer2_core_processes.controller.controller import Controller
from jonbot.layer2_data_layer.data_models.conversation_models import ChatInput, ChatResponse

app = FastAPI()

@app.post("/chat")
def chat(chat_input: ChatInput) -> ChatResponse:
    """
    Process the chat input
    """

    response = Controller().handle_chat_input(chat_input)
    return response

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
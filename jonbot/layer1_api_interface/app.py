
from fastapi import FastAPI


from jonbot.layer2_core_processes.controller.controller import Controller
from jonbot.layer3_data_layer.data_models.conversation_models import ChatInput, ChatResponse

app = FastAPI()
controller = Controller()
@app.post("/chat")
def chat(message: str) -> ChatResponse:
    """
    Process the chat input
    """

    response = controller.handle_chat_input(user_message=message)
    return response

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
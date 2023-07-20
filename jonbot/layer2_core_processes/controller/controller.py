from pydantic import BaseModel

from jonbot.layer2_data_layer.data_models.conversation_models import ChatInput, ChatResponse, \
    ChatInteraction
from jonbot.layer2_data_layer.database.json_database import JSONDatabase


class Controller(BaseModel):
    """
    Handles communication with the API layer, gets data from the database, sends `request+ parameters + data` 
    to `processing` sublayer, and then returns results to the API and database layers.
    """
    json_database: JSONDatabase = JSONDatabase()

    class Config:
        arbitrary_types_allowed = True
    def handle_chat_input(input: ChatInput) -> ChatResponse:
        """
        Process the chat input
        """

        # Perform any necessary processing on the chat input
        # Save the data to the database
        bot_response = ChatResponse(message='Wowo, hello!')
        chat_response = ChatInteraction(human_input=input,
                                        bot_response=bot_response)


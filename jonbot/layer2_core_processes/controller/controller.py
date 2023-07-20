from pydantic import BaseModel

from jonbot.layer3_data_layer.data_models.conversation_models import ChatInput, ChatResponse, \
    ChatInteraction
from jonbot.layer3_data_layer.database.json_database import JSONDatabase

from jonbot.layer2_core_processes.processing_sublayer.get_bot_response import get_bot_response

class Controller(BaseModel):
    """
    Handles communication with the API layer, gets data from the database, sends `request+ parameters + data` 
    to `processing` sublayer, and then returns results to the API and database layers.
    """
    json_database: JSONDatabase = JSONDatabase()

    class Config:
        arbitrary_types_allowed = True
    def handle_chat_input(self, user_message: str) -> ChatResponse:
        """
        Process the chat input
        """

        # Perform any necessary processing on the chat input
        # Save the data to the database
        response_message = get_bot_response(input = user_message)
        bot_response = ChatResponse(message=response_message)
        chat_interaction = ChatInteraction(human_input=ChatInput(message=user_message),
                                            bot_response = bot_response)
        self.json_database.add_interaction_to_conversation(conversation_id="conversation_id", interaction=chat_interaction)
        return bot_response




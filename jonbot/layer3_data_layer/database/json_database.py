import json
from pathlib import Path

from pydantic import BaseModel

from jonbot.layer3_data_layer.data_models.application_data_model import ApplicationDataModel
from jonbot.layer3_data_layer.data_models.conversation_models import ChatInteraction

JSON_DATABASE_FILENAME = 'jonbot_data.json'
class JSONDatabase:
    def __init__(self):
        self.json_file_path = Path().home() / JSON_DATABASE_FILENAME

        try:

            if not self.json_file_path.exists():
                self.json_file_path.touch()
        except Exception as e:
            print(f"Error creating JSON database file: {e}")
            raise e

        self._application_data_model = self.load_data()
        self._users = self._application_data_model.users
        self._conversations = self._application_data_model.conversations
        self._settings = self._application_data_model.settings


    def log_user(self, user_id: str):
        if user_id not in self._users:
            self._users[user_id] = UserModel(user_id=user_id)
            self.save_data(self._application_data_model)

    def log_conversation(self, conversation_id: str):
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = ConversationModel(conversation_id=conversation_id)
            self.save_data(self._application_data_model)

    def add_interaction_to_conversation(self, conversation_id: str, interaction: ChatInteraction):
        self._conversations[conversation_id].interactions.append(interaction)
        self.save_data(self._application_data_model)

    def save_data(self, data: BaseModel):
        """
        Save data to the JSON file
        """
        try:
            self.json_file_path.write_text(json.dumps(data.model_dump_json(indent=4)))
        except Exception as e:
            print(f"Error saving JSON database file: {e}")
            raise e

    def load_data(self) -> ApplicationDataModel:
        """
        Load data from the JSON file
        """
        try:
            with open(self.json_file_path, 'r') as f:
                application_data = json.load(f)
        except json.JSONDecodeError:  # Handle empty file
            return ApplicationDataModel()
        except Exception as e:
            print(f"Error loading JSON database file: {e}")
            raise e

        return ApplicationDataModel(**application_data)
import json
from pathlib import Path

from pydantic import BaseModel

from jonbot.layer3_data_layer.data_models.application_data_model import ApplicationDataModel
from jonbot.layer3_data_layer.data_models.conversation_models import ChatInteraction, ConversationModel
from jonbot.layer3_data_layer.data_models.user_data_model import UserModel

BASE_DIRECTORY = 'jonbot_data'
JSON_DATABASE_FILE_NAME = "jonbot_data.json"


class JSONDatabase:

    def __init__(self):
        self.json_file_path = Path().home() / BASE_DIRECTORY / JSON_DATABASE_FILE_NAME

        self.json_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.json_file_path.touch(exist_ok=True)

        self._application_data_model = self.load_data()
        self._users = self._application_data_model.users
        self._conversations = self._application_data_model.conversations
        self._settings = self._application_data_model.settings

        # If the JSON file was empty, save the initialized model
        if not self._users and not self._conversations and not self._settings:
            self.save_data(self._application_data_model)

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
            self.json_file_path.write_text(data.model_dump_json(indent=4))
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

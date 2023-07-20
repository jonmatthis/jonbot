import json
from pathlib import Path

from pydantic import BaseModel

from jonbot.layer2_data_layer.data_models.application_data_model import ApplicationDataModel

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
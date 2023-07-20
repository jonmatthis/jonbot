import uuid

import requests
from rich import print
from rich.prompt import Prompt

from jonbot.layer2_data_layer.data_models.conversation_models import ChatInput, Timestamp


def run_cli():
    """
    Run the command line interface for JonBot
    """
    session_id = str(f"session_{uuid.uuid4()}")
    while True:
        message = Prompt.ask('Enter your message (type "quit" to exit):')
        if message == 'quit':
            break
        url = 'http://localhost:8000/chat'
        chat_input = ChatInput(message=message,
                               message_id=str(uuid.uuid4()),
                               metadata={'session_id': session_id,
                                        'timestamp': Timestamp().model_dump(),
                                         }

                               )
        response = requests.post(url, json=chat_input.model_dump_json())
        print(f"Response: {response.json()}")


if __name__ == '__main__':
    run_cli()

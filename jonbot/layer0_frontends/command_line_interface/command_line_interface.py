import uuid

import requests
from rich import print
from rich.prompt import Prompt
from rich.pretty import pprint

from jonbot.layer3_data_layer.data_models.conversation_models import ChatInput, Timestamp

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
                               metadata={'session_id': session_id,
                                         'timestamp': Timestamp().model_dump(),
                                         }
                               )
        response = requests.post(url, json=chat_input.model_dump())
        print("[bold green]Response:[/bold green]")
        pprint(response.json())

if __name__ == '__main__':
    run_cli()

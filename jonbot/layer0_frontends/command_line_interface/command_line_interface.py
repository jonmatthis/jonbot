import logging
import uuid

import requests
from rich import print
from rich.pretty import pprint
from rich.prompt import Prompt

from jonbot.layer3_data_layer.data_models.conversation_models import ChatInput
from jonbot.layer3_data_layer.data_models.timestamp_model import Timestamp

logger = logging.getLogger(__name__)


def run_cli():
    """
    Run the command line interface for JonBot
    """
    logger.info("Starting command line interface")
    session_id = str(f"session_{uuid.uuid4()}")
    url = 'http://localhost:8000/chat'
    print(f"Starting session {session_id}")
    while True:
        message = Prompt.ask('Enter your message (type "quit" to exit):')

        if message == 'quit':
            logger.info("Exiting command line interface")
            break

        chat_input = ChatInput(message=message,
                               metadata={'session_id': session_id,
                                         'timestamp': Timestamp().model_dump(),
                                         }
                               )
        logger.info(f"Sending chat input: {chat_input.model_dump()}")

        response = requests.post(url, json=chat_input.model_dump())
        print("[bold green]Response:[/bold green]")
        logger.info(f"Sending message: {message}")
        pprint(response.json())


if __name__ == '__main__':
    logger.info("Starting command line interface")
    run_cli()

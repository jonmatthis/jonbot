import logging
from concurrent.futures import ThreadPoolExecutor
from jonbot.layer0_frontends.discord_bot.discord_main import run_discord_client
from jonbot.layer1_api_interface.app import run_api

logger = logging.getLogger(__name__)

def run_services():
    """
    Run the Discord bot and the API server.
    """
    with ThreadPoolExecutor() as executor:
        # Start the Discord bot in a new thread
        discord_bot_thread = executor.submit(run_discord_client)

        # Start the API server in a new thread
        api_server_thread = executor.submit(run_api)

        # Wait for the threads to complete
        discord_bot_thread.result()
        api_server_thread.result()

if __name__ == "__main__":
    run_services()

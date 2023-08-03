import logging
from multiprocessing import Process

from jonbot.layer0_frontends.discord_bot.discord_main import run_discord_client
from jonbot.layer1_api_interface.app import run_api

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Start the Discord bot in a new thread
    discord_bot_process = Process(target=run_discord_client)
    discord_bot_process.start()

    # Start the API server in a new process
    api_server_process = Process(target=run_api)
    api_server_process.start()

    discord_bot_process.join()
    api_server_process.join()

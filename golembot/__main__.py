import logging
from concurrent.futures import ProcessPoolExecutor

from golembot.layer0_frontends.discord_bot.discord_main import run_discord_bot
from golembot.layer0_frontends.telegram_bot.telegram_bot import run_telegram_bot_sync
from golembot.layer1_api_interface.app import run_api_sync

logger = logging.getLogger(__name__)
def run_services():
    """
    Run the Discord bot and the API server.
    """

    with ProcessPoolExecutor() as executor:
        # Start the Discord bot in a new thread
        discord_bot_thread = executor.submit(run_discord_bot)

        # Start the API server in a new thread
        api_server_thread = executor.submit(run_api_sync)

        # Start the Telegram bot using asyncio
        telegram_bot_thread = executor.submit(run_telegram_bot_sync)

        # Wait for the threads to complete
        discord_bot_thread.result()
        api_server_thread.result()
        telegram_bot_thread.result()
def main():
    run_services()

if __name__ == "__main__":
    main()

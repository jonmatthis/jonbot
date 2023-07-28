import logging
import concurrent.futures

from jonbot.layer0_frontends.discord_bot.bot_main import run_discord_bot

logger = logging.getLogger(__name__)


def main() -> None:
    """
    Main function to start the bot and run API.

    This function starts the bot and runs the API in a ThreadPool.

    Returns:
        None
    """
    logger.info("Starting JonBot")

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        try:
            from jonbot.layer1_api_interface.app import run_api

            futures = [executor.submit(run_api), executor.submit(run_discord_bot)]

            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Exception occured in thread {e}")
        except Exception as e:
            logger.error(f"Failed to create thread: {e}")


if __name__ == '__main__':
    main()

from concurrent.futures import ProcessPoolExecutor

from jonbot import configure_logging
from jonbot.layer0_frontends.discord_bot.discord_main import run_discord_bot
from jonbot.layer0_frontends.telegram_bot.telegram_bot import run_telegram_bot_sync
from jonbot.layer1_api_interface.api_main import run_api_sync
from jonbot.system.logging.get_or_create_logger import logger


SERVICES = [
    run_discord_bot,
    run_api_sync,
    run_telegram_bot_sync
]


def run_services():
    """
    Run the Discord bot, the API server, and the Telegram bot.
    """
    logger.info("Starting Services...")
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(service) for service in SERVICES]

        for future in futures:
            try:
                result = future.result()
                if result is not None and not result:
                    raise ValueError(f"{future} reported failure")
            except Exception as e:
                logger.error(f"Error encountered: {e}")
                for other_future in futures:
                    if not other_future.done():
                        other_future.cancel()
                raise


def main():
    # Initializing logging for the main process.
    # If each process needs a separate log, initialize inside the service function.
    configure_logging()
    logger.info("Starting jonbot...")
    run_services()


if __name__ == "__main__":
    main()

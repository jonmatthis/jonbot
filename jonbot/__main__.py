from concurrent.futures import ProcessPoolExecutor

from jonbot import get_logger
from jonbot.layer0_frontends.discord_bot.discord_main import run_discord_bot
from jonbot.layer0_frontends.telegram_bot.telegram_bot import run_telegram_bot_sync
from jonbot.layer1_api_interface.api_main import run_api_sync
from jonbot.system.environment_variables import BOT_NICK_NAMES

logger = get_logger()


# Note: At the end, the final SERVICES list will be built dynamically
BASE_SERVICES = [
    {"func": run_api_sync},
]

def run_services():
    """
    Run the Discord bot, the API server, and the Telegram bot.
    """
    logger.info("Starting Services...")

    # Dynamically create service tasks based on BOT_NICK_NAMES
    SERVICES = BASE_SERVICES.copy()
    for bot_name in BOT_NICK_NAMES:
        SERVICES.append({"func": run_discord_bot, "kwargs": {"bot_name_or_index": bot_name}})
        SERVICES.append({"func": run_telegram_bot_sync, "kwargs": {"bot_name_or_index": bot_name}})

    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(service["func"], **service.get("kwargs", {})) for service in SERVICES]

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
    logger.info("Starting services...")
    run_services()

if __name__ == "__main__":
    main()

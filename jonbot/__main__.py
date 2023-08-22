import os
from concurrent.futures import ProcessPoolExecutor
from typing import Optional, List

from jonbot import get_logger
from jonbot.layer0_frontends.discord_bot.discord_main import run_discord_bot
from jonbot.layer0_frontends.telegram_bot.telegram_bot import run_telegram_bot_sync
from jonbot.layer1_api_interface.api_main import run_api_sync
from jonbot.system.environment_variables import BOT_NICK_NAMES

logger = get_logger()


def run_services(services):
    """
    Run the Discord bot, the API server, and the Telegram bot.
    """
    logger.info("Starting Services...")

    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(service["func"], **service.get("kwargs", {})) for service in services]

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


def create_services(selection: Optional[str]) -> List:
    if selection is None:
        selection = "all"
    selection = selection.lower()

    services = []

    # Creating services based on selection
    if selection in ["discord", "all"]:
        services.extend(create_discord_services())
    # if selection in ["telegram", "all"]:
    #     services.extend(create_telegram_services()) # Uncomment when create_telegram_services is defined
    if selection in ["api", "all"]:
        services.append({"func": run_api_sync})

    return services


def create_discord_services():
    bots = []

    for bot_name in BOT_NICK_NAMES:
        bots.append({"func": run_discord_bot, "kwargs": {"bot_name_or_index": bot_name}})
    return bots


def create_telegram_services():
    bots = []
    for bot_name in BOT_NICK_NAMES:
        bots.append({"func": run_telegram_bot_sync, "kwargs": {"bot_name_or_index": bot_name}})
    return bots


def get_run_services_selection() -> Optional[str]:
    selection = os.getenv("RUN_SERVICES")
    return selection


def main():
    # Initializing logging for the main process.
    # If each process needs a separate log, initialize inside the service function.
    logger.info("Starting services...")
    selection = get_run_services_selection()
    services = create_services(selection=selection)
    run_services(services)


if __name__ == "__main__":
    main()

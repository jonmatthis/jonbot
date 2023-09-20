import os
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv

from jonbot.api_interface.api_main import run_api_sync
from jonbot.frontends.discord_bot.discord_main import run_discord_bot
from jonbot.system.setup_logging.get_logger import get_jonbot_logger
from jonbot.system.startup.named_process import NamedProcess

logger = get_jonbot_logger()


def startup(bot_nick_names: List[str]):
    bot_nick_names = filter_bot_nick_names(bot_nick_names=bot_nick_names)
    logger.info("Starting services...")
    selection = get_services_selection()
    logger.info(f"Selected services: {selection}")
    services = create_services(selected_services=selection,
                               bot_nick_names=bot_nick_names)
    logger.info(f"Services to run: {services}")
    run_services(services)


def run_services(services: List[Dict[str, Any]]):
    """
    Run the Discord bot, the API server, and the Telegram bot.
    """
    logger.info(f"Starting Services: {services}")

    if not services:
        raise ValueError("No services provided!")

    processes = []
    for service in services:
        process_name = f"{service['func'].__name__}__{service.get('kwargs', {}).get('bot_name_or_index', '')}"
        process = NamedProcess(
            target=service["func"], name=process_name, kwargs=service.get("kwargs", {})
        )
        processes.append(process)

    # Start the processes
    for process in processes:
        process.start()

    # Join the processes
    for process in processes:
        process.join()

        if not process.exitcode:
            logger.error(f"Process {process.custom_name} reported failure")
            # Terminate other processes if one failed
            for other_process in processes:
                other_process.terminate()


def create_services(selected_services: str,
                    bot_nick_names: List[str]) -> List:
    selected_services = selected_services.lower()
    logger.trace(f"Creating services for `selected_services.lower()`: {selected_services}")
    services = []

    # Creating services based on selection
    if selected_services in ["discord", "all"]:
        services.extend(create_discord_services(bot_nick_names=bot_nick_names))
    else:
        logger.debug(f"selected_services: {selected_services} not in ['discord', 'all']")

    if selected_services in ["api", "all"]:
        services.append({"func": run_api_sync})
    else:
        logger.debug(f"selected_services: {selected_services} not in ['discord', 'all']")

    logger.trace(f"Created services: {services}")
    if len(services) == 0:
        raise ValueError("No services selected")

    return services


def create_discord_services(bot_nick_names: List[str]):
    bots = []

    for bot_name in bot_nick_names:
        bots.append(
            {"func": run_discord_bot, "kwargs": {"bot_name_or_index": bot_name}}
        )
    return bots


def filter_bot_nick_names(bot_nick_names: List[str]) -> List[str]:
    if not os.getenv("IS_DOCKER"):
        if len(bot_nick_names) > 2:
            return bot_nick_names[:2]  # when running locally, only run the first two bots

    return bot_nick_names


def get_services_selection() -> Optional[str]:
    if not os.getenv("IS_DOCKER"):
        load_dotenv()

    load_dotenv()
    selection = os.getenv("RUN_SERVICES")
    if not selection:
        raise EnvironmentError("Could not find `RUN_SERVICES` environment variable")
    return selection

import multiprocessing
import os
from typing import Optional, List

from jonbot import get_logger
from jonbot.layer0_frontends.discord_bot.discord_main import run_discord_bot
from jonbot.layer0_frontends.telegram_bot.telegram_bot import run_telegram_bot_sync
from jonbot.layer1_api_interface.api_main import run_api_sync
from jonbot.system.environment_variables import BOT_NICK_NAMES

logger = get_logger()


def startup():
    logger.info("Starting services...")
    selection = get_services_selection()
    logger.info(f"Selected services: {selection}")
    services = create_services(selection=selection)
    logger.info(f"Services to run: {services}")
    run_services(services)



class NamedProcess(multiprocessing.Process):
    def __init__(self, *args, name=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_name = name

    def run(self):
        # Set the process name (visible in system tools like top/htop on Unix)
        # Note: This step is optional
        if self.custom_name:
            multiprocessing.current_process().name = self.custom_name
        super().run()


def run_services(services):
    """
    Run the Discord bot, the API server, and the Telegram bot.
    """
    logger.info(f"Starting Services: {services}")

    processes = []
    for service in services:
        process_name = f"{service['func'].__name__}__{service.get('kwargs', {}).get('bot_name_or_index', '')}"
        process = NamedProcess(target=service["func"], name=process_name, kwargs=service.get("kwargs", {}))
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


def get_services_selection() -> Optional[str]:
    selection = os.getenv("RUN_SERVICES")
    return selection

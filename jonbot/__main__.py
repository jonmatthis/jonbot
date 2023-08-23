from jonbot import get_logger
from jonbot.startup.startup_processes import run_services, create_services, get_services_selection

logger = get_logger()


def main():
    # Initializing logging for the main process.
    # If each process needs a separate log, initialize inside the service function.
    logger.info("Starting services...")
    selection = get_services_selection()
    logger.info(f"Selected services: {selection}")
    services = create_services(selection=selection)
    logger.info(f"Services to run: {services}")
    run_services(services)


if __name__ == "__main__":
    main()

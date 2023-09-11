from jonbot.system.setup_logging.get_logger import get_jonbot_logger
from jonbot.system.startup.startup_processes import startup

logger = get_jonbot_logger()


def main():
    logger.info("Starting up...")
    startup()


if __name__ == "__main__":
    logger.debug("Running __main__.py...")
    main()

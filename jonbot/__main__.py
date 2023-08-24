from jonbot import get_logger
from jonbot.startup.startup_processes import startup

logger = get_logger()


def main():
    logger.info("Starting up...")
    startup()


if __name__ == "__main__":
    logger.debug("Running __main__.py...")
    main()

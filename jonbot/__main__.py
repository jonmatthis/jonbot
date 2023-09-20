import argparse
import os
from typing import List

from jonbot.system.setup_logging.get_logger import get_jonbot_logger
from jonbot.system.startup.startup_processes import startup

logger = get_jonbot_logger()


def main(bot_nick_names: List[str]):
    logger.info("Starting up...")
    startup(bot_nick_names=bot_nick_names)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("bot_nick_name",
                        type=str,
                        help="The nick_name of the bot to run (must be in os.getenv('BOT_NICK_NAMES'))",
                        nargs="?",
                        default="")
    args = parser.parse_args()
    if args.bot_nick_name == "":
        from jonbot.system.environment_variables import BOT_NICK_NAMES

        bot_nick_names = BOT_NICK_NAMES
    else:
        bot_nick_names = args.bot_nick_name.split(",")

    logger.debug("Running __main__.py...")
    main(bot_nick_names=bot_nick_names)

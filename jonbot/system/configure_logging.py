import inspect
import logging
import logging.handlers
import sys
from logging.config import dictConfig

from jonbot.system.path_getters import get_log_file_path

DEFAULT_LOGGING = {"version": 1, "disable_existing_loggers": False}

format_string = "[%(asctime)s.%(msecs)04d] [%(levelname)8s] [%(name)s] [%(funcName)s():%(lineno)s] [PID:%(process)d TID:%(thread)d] %(message)s"
default_logging_formatter = logging.Formatter(fmt=format_string, datefmt="%Y-%m-%dT%H:%M:%S")

LOG_FILE_PATH = None
TRACE = 5
logging.addLevelName(TRACE, "TRACE")
logging.root.setLevel(TRACE)



# Add the method for the new TRACE level
def trace(self, message, *args, **kws):
    if self.isEnabledFor(TRACE):
        self._log(TRACE, message, args, **kws)


logging.Logger.trace = trace





def get_logging_handlers():
    dictConfig(DEFAULT_LOGGING)
    console_handler = build_console_handler()
    file_handler = build_file_handler()

    return [file_handler,
            console_handler]




def build_file_handler():
    file_handler = logging.FileHandler(get_log_file_path(), encoding="utf-8")
    file_handler.setLevel(TRACE)
    file_handler.setFormatter(default_logging_formatter)
    return file_handler


class ColoredConsoleHandler(logging.StreamHandler):
    COLORS = {
        "TRACE": "\033[37m",  # Dark White (equivalent to gray)
        "DEBUG": "\033[34m",  # Blue
        "INFO": "\033[36m",  # Dark Cyan
        "WARNING": "\033[33m",  # YELLOW
        "ERROR": "\033[31m",  # RED
        "CRITICAL": "\033[41m",  # BG RED
    }

    def emit(self, record):
        # Set the color for this record
        color_code = self.COLORS.get(record.levelname, "\033[0m")

        # Format the record with color
        formatted_record = color_code + self.format(record) + "\033[0m"  # \033[0m resets the color

        # Print the colored record to console
        print(formatted_record)


def build_console_handler():
    console_handler = ColoredConsoleHandler(stream=sys.stdout)
    console_handler.setLevel(TRACE)
    console_handler.setFormatter(default_logging_formatter)
    return console_handler


def configure_logging():
    print(f"Setting up logging  {__file__}")

    if len(logging.getLogger().handlers) == 0:
        handlers = get_logging_handlers()
        for handler in handlers:
            if not handler in logging.getLogger("").handlers:
                logging.getLogger("").handlers.append(handler)
    else:
        logger = logging.getLogger(__name__)
        logger.info("Logging already configured")


def log_test_messages():
    logger = logging.getLogger(__name__)
    logger.trace("This is a TRACE message.")
    logger.debug("This is a DEBUG message.")
    logger.info("This is an INFO message.")
    logger.warning("This is a WARNING message.")
    logger.error("This is an ERROR message.")
    logger.critical("This is a CRITICAL message.")

if __name__ == "__main__":
    # configure the logging
    configure_logging()
    log_test_messages()

    print("Logging setup and tests completed. Check the console output and the log file.")

import inspect
import logging
import logging.handlers
import sys
from logging.config import dictConfig
from pathlib import Path

from jonbot.system.path_getters import get_base_data_folder_path, LOG_FILE_FOLDER_NAME, \
    create_log_file_name

DEFAULT_LOGGING = {"version": 1, "disable_existing_loggers": False}

LOG_FILE_PATH = None
TRACE_LEVEL = 5
logging.addLevelName(TRACE_LEVEL, "TRACE")
logging.root.setLevel(TRACE_LEVEL)


# Add the method for the new TRACE level
def trace(self, message, *args, **kws):
    if self.isEnabledFor(TRACE_LEVEL):
        self._log(TRACE_LEVEL, message, args, **kws)

logging.Logger.trace = trace


class CustomFormatter(logging.Formatter):
    def format(self, record):
        # You can add custom attributes here, like:
        frame = inspect.stack()[8]
        record.caller_name = frame[1]
        record.caller_funcName = frame[3]
        record.caller_lineno = frame[2]
        return super().format(record)

# Then, use the custom formatter:
format_string = "[%(asctime)s.%(msecs)04d] [%(levelname)8s] [%(caller_name)s] [%(caller_funcName)s():%(caller_lineno)s] [PID:%(process)d TID:%(thread)d] %(message)s"
custom_formatter = CustomFormatter(fmt=format_string, datefmt="%Y-%m-%dT%H:%M:%S")


def get_logging_handlers():
    dictConfig(DEFAULT_LOGGING)
    console_handler = build_console_handler()
    file_handler = build_file_handler()

    return [file_handler,
            console_handler]


def get_log_file_path():
    log_folder_path = Path(get_base_data_folder_path()) / LOG_FILE_FOLDER_NAME
    log_folder_path.mkdir(exist_ok=True, parents=True)
    log_file_path = log_folder_path / create_log_file_name()
    return str(log_file_path)


def build_file_handler():
    file_handler = logging.FileHandler(get_log_file_path(), encoding="utf-8")
    file_handler.setLevel(TRACE_LEVEL)
    file_handler.setFormatter(custom_formatter)
    return file_handler


class ColoredConsoleHandler(logging.StreamHandler):
    COLORS = {
        "TRACE": "\033[37m",  # Dark White (equivalent to gray)
        "DEBUG": "\033[36m",  # Dark Cyan
        "INFO": "\033[34m",  # Blue
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
    console_handler.setLevel(TRACE_LEVEL)
    console_handler.setFormatter(custom_formatter)
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







if __name__ == "__main__":
    # configure the logging
    configure_logging()
    logger = logging.getLogger(__name__)
    # log some test messages
    logger.trace("This is a TRACE message.")
    logger.debug("This is a DEBUG message.")
    logger.info("This is an INFO message.")
    logger.warning("This is a WARNING message.")
    logger.error("This is an ERROR message.")
    logger.critical("This is a CRITICAL message.")

    print("Logging setup and tests completed. Check the console output and the log file.")

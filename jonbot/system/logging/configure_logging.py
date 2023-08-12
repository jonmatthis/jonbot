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


class ContextLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        # Enhance the log record with new attributes
        kwargs['extra'] = {
            'caller_name': self.extra['caller_name'],
            'caller_funcName': self.extra['caller_funcName'],
            'caller_lineno': self.extra['caller_lineno']
        }
        return msg, kwargs

    # Add the trace method to the ContextLoggerAdapter
    def trace(self, msg, *args, **kwargs):
        self.log(TRACE_LEVEL, msg, *args, **kwargs)


format_string = "[%(asctime)s.%(msecs)04d] [%(levelname)8s] [%(caller_name)s] [%(caller_funcName)s():%(caller_lineno)s] [PID:%(process)d TID:%(thread)d] %(message)s"

default_logging_formatter = logging.Formatter(fmt=format_string, datefmt="%Y-%m-%dT%H:%M:%S")


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
    file_handler.setFormatter(default_logging_formatter)
    return file_handler


class ColoredConsoleHandler(logging.StreamHandler):
    COLORS = {
        "TRACE": "\033[0m",  # DEFAULT
        "DEBUG": "\033[0m",  # DEFAULT
        "INFO": "\033[0m",  # DEFAULT
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
    console_handler.setFormatter(default_logging_formatter)
    return console_handler


def configure_logging(entry_point: str = None):
    print(f"Setting up logging  {__file__}")

    if len(logging.getLogger().handlers) == 0:
        handlers = get_logging_handlers()
        for handler in handlers:
            if not handler in logging.getLogger("").handlers:
                logging.getLogger("").handlers.append(handler)
    else:
        logger.info("Logging already configured")


LOGGER = None


def get_or_create_logger():
    logger = logging.getLogger(__name__)
    caller_frame = sys._getframe(1)  # Get one frame back to the caller
    adapter = ContextLoggerAdapter(
        logger,
        {
            'caller_name': caller_frame.f_globals['__name__'],
            'caller_funcName': caller_frame.f_code.co_name,
            'caller_lineno': caller_frame.f_lineno
        }
    )
    return adapter


logger = get_or_create_logger()

if __name__ == "__main__":
    # configure the logging
    configure_logging(entry_point=__name__)

    # log some test messages
    logger.trace("This is a TRACE message.")
    logger.debug("This is a DEBUG message.")
    logger.info("This is an INFO message.")
    logger.warning("This is a WARNING message.")
    logger.error("This is an ERROR message.")
    logger.critical("This is a CRITICAL message.")

    print("Logging setup and tests completed. Check the console output and the log file.")

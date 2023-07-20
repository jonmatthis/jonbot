import io
import logging
import logging.handlers
import sys
from logging.config import dictConfig
from pathlib import Path

from jonbot.layer3_data_layer.system.filenames_and_paths import get_base_data_folder_path, LOG_FILE_FOLDER_NAME, \
    create_log_file_name

DEFAULT_LOGGING = {"version": 1, "disable_existing_loggers": False}

LOG_FILE_PATH = None

format_string = "[%(asctime)s.%(msecs)04d] [%(levelname)8s] [%(name)s] [%(funcName)s():%(lineno)s] [PID:%(process)d TID:%(thread)d] %(message)s"

default_logging_formatter = logging.Formatter(fmt=format_string, datefmt="%Y-%m-%dT%H:%M:%S")


def get_logging_handlers(entry_point: str = None):
    dictConfig(DEFAULT_LOGGING)

    console_handler = build_console_handler()
    file_handler = build_file_handler()

    if not entry_point == "cli":
        return [console_handler, file_handler]

    return [file_handler]

def get_log_file_path():
    log_folder_path = Path(get_base_data_folder_path()) / LOG_FILE_FOLDER_NAME
    log_folder_path.mkdir(exist_ok=True, parents=True)
    log_file_path = log_folder_path / create_log_file_name()
    return str(log_file_path)

def build_file_handler():
    file_handler = logging.FileHandler(get_log_file_path(), encoding="utf-8")
    file_handler.setFormatter(default_logging_formatter)
    file_handler.setLevel(logging.DEBUG)
    return file_handler


def build_console_handler():
    stream = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    console_handler = logging.StreamHandler(stream)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(default_logging_formatter)
    return console_handler


def configure_logging(entry_point: str = None):
    print(f"Setting up logging  {__file__}")

    if len(logging.getLogger().handlers) == 0:
        handlers = get_logging_handlers(entry_point=entry_point)
        for handler in handlers:
            if not handler in logging.getLogger("").handlers:
                logging.getLogger("").handlers.append(handler)

        logging.root.setLevel(logging.DEBUG)
    else:
        logger = logging.getLogger(__name__)
        logger.info("Logging already configured")

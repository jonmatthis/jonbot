import logging
import sys
from datetime import datetime
from enum import Enum
from logging.config import dictConfig

from jonbot.system.path_getters import get_log_file_path


class LogLevel(Enum):
    TRACE = 5
    DEBUG = logging.DEBUG  # 10
    INFO = logging.INFO  # 20
    SUCCESS = 25
    WARNING = logging.WARNING  # 30
    ERROR = logging.ERROR  # 40
    CRITICAL = logging.CRITICAL  # 50


logging.addLevelName(LogLevel.TRACE.value, "TRACE")
logging.addLevelName(LogLevel.SUCCESS.value, "SUCCESS")









class MicrosecondFormatter(logging.Formatter):
    """A custom Formatter class to include microseconds in log timestamps."""

    def formatTime(self, record, datefmt=None):
        created = record.created
        if isinstance(created, float) or isinstance(created, int):
            timestamp = created
        else:
            raise TypeError("Invalid type for 'created'")

        date_format_with_microseconds = "%Y-%m-%dT%H:%M:%S.%f"  # Including microseconds with %f
        return datetime.strftime(datetime.fromtimestamp(timestamp), date_format_with_microseconds)


class LoggerBuilder:
    DEFAULT_LOGGING = {"version": 1, "disable_existing_loggers": False}
    format_string = ("[%(asctime)s] [%(levelname)8s] [%(name)s] "
                     "[%(funcName)s():%(lineno)s] [PID:%(process)d TID:%(thread)d] %(message)s")

    def __init__(self, level: LogLevel):
        self.default_logging_formatter = MicrosecondFormatter(
            fmt=self.format_string, datefmt="%Y-%m-%dT%H:%M:%S")
        dictConfig(self.DEFAULT_LOGGING)

        self._set_logging_level(level)

    def _set_logging_level(self, level: LogLevel):
        logging.root.setLevel(level.value)



    def build_file_handler(self):
        file_handler = logging.FileHandler(get_log_file_path(), encoding="utf-8")
        file_handler.setLevel(LogLevel.TRACE.value)
        file_handler.setFormatter(self.default_logging_formatter)
        return file_handler

    class ColoredConsoleHandler(logging.StreamHandler):
        COLORS = {
            "TRACE": "\033[37m",  # Dark White (grey)
            "DEBUG": "\033[34m",  # Blue
            "INFO": "\033[96m",  # Cyan
            "SUCCESS": "\033[95m",  # Magenta
            "WARNING": "\033[33m",  # Yellow
            "ERROR": "\033[31m",  # Red
            "CRITICAL": "\033[41m",  # Background Red
        }

        def emit(self, record):
            color_code = self.COLORS.get(record.levelname, "\033[0m")
            formatted_record = color_code + self.format(record) + "\033[0m"
            print(formatted_record)

    def build_console_handler(self):
        console_handler = self.ColoredConsoleHandler(stream=sys.stdout)
        console_handler.setLevel(LogLevel.TRACE.value)
        console_handler.setFormatter(self.default_logging_formatter)
        return console_handler

    def configure(self):
        if len(logging.getLogger().handlers) == 0:
            handlers = [self.build_file_handler(), self.build_console_handler()]
            for handler in handlers:
                if handler not in logging.getLogger("").handlers:
                    logging.getLogger("").handlers.append(handler)
        else:
            from jonbot import get_logger
            logger = get_logger()
            logger.info("Logging already configured")


def configure_logging(level: LogLevel = LogLevel.INFO):
    def trace(self, message, *args, **kws):
        if self.isEnabledFor(LogLevel.TRACE.value):
            self._log(LogLevel.TRACE.value, message, args, **kws)

    logging.Logger.trace = trace

    def success(self, message, *args, **kws):
        if self.isEnabledFor(LogLevel.SUCCESS.value):
            self._log(LogLevel.SUCCESS.value, message, args, **kws)

    logging.Logger.success = success

    builder = LoggerBuilder(level)
    builder.configure()


def log_test_messages():
    from jonbot import get_logger
    logger = get_logger()
    logger.trace("This is a TRACE message.")
    logger.debug("This is a DEBUG message.")
    logger.info("This is an INFO message.")
    logger.success("This is a SUCCESS message.")
    logger.warning("This is a WARNING message.")
    logger.error("This is an ERROR message.")
    logger.critical("This is a CRITICAL message.")


if __name__ == "__main__":
    configure_logging(LogLevel.TRACE)  # Setting the root logger level to TRACE
    log_test_messages()
    print("Logging setup and tests completed. Check the console output and the log file.")

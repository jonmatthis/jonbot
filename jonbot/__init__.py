"""A simple bot what for to talk to 🤖❤️✨"""
__version__ = "v1.4.0"

import logging

from jonbot.system.setup_logging.configure_logging import LogLevel, configure_logging

configure_logging(LogLevel.TRACE)
logger = logging.getLogger(__name__)

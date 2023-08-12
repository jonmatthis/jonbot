
LOGGER = None

import logging

class ContextLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        # Enhance the log record with new attributes
        kwargs['extra'] = {
            'caller_name': self.extra['caller_name'],
            'caller_funcName': self.extra['caller_funcName'],
            'caller_lineno': self.extra['caller_lineno']
        }
        return msg, kwargs

def get_or_create_logger():
    logger = logging.getLogger(__name__)
    caller_frame = logging.currentframe().f_back  # Get one frame back to the caller
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
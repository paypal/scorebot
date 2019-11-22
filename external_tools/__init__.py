import logging
from .version import __version__

# Version
VERSION = __version__

# Set default logging handler to avoid "No handler found" warnings.
try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())


def add_stderr_logger(logger=None, level=logging.DEBUG):
    """
    Helper for quickly adding a StreamHandler to the logger. Useful for debugging.

    Returns the logger after adding it.
    """
    # This method needs to be in this __init__.py to get the __name__ correct
    # even if urllib3 is vendored within another package.
    if logger is None:
        logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.debug('Added an stderr logging handler to logger: %s' % __name__)
    return logger


del NullHandler

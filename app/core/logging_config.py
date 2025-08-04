import logging
import sys


LOG_LEVEL = logging.getLevelName("INFO")


def configure_logging():
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    root_logger.setLevel(LOG_LEVEL) 
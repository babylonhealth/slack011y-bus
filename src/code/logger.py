import json
import logging
import os
from collections import OrderedDict

LOG_LEVEL: int = logging.INFO if os.getenv("DEBUG", "false") == "false" else logging.DEBUG


def create_logger(name: str) -> logging.Logger:
    logger: logging.Logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    logger.handlers = []
    logger.propagate = False
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        json.dumps(
            OrderedDict(
                [
                    ("@timestamp", "%(asctime)s"),
                    ("logger_name", "slack-bot-app"),
                    ("module_name", "%(module)s"),
                    ("function", "%(funcName)s"),
                    ("pid", "%(process)d"),
                    ("pname", "%(processName)s"),
                    ("level", "%(levelname)s"),
                    ("message", "%(message)s"),
                ]
            )
        ),
        "%Y-%m-%dT%H:%M:%S%z",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

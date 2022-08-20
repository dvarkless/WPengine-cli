import logging
import sys
import traceback

from constants import LOG_PATH


def handle_exception(type, value, traceback_info):
    if issubclass(type, KeyboardInterrupt):
        sys.__excepthook__(type, value, traceback_info)
        return
    text = "".join(traceback.format_exception(type, value, traceback_info))
    print(text)

    logging.basicConfig(filename=LOG_PATH)
    logging.error(f"Uncaught exception: {text}")

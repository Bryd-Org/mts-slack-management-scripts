import logging
import os
from logging.handlers import TimedRotatingFileHandler

from dynaconf import Dynaconf

settings = Dynaconf(
    env="default",
    environments=True,
    default_settings_paths=["settings.toml", ".secrets.toml"],
    ROOT_PATH_FOR_DYNACONF=os.path.abspath(os.getcwd()),
)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


LOG_FILENAME = "/tmp/python.log"

root = logging.getLogger()
for handler in list(root.handlers):
    root.removeHandler(handler)

log = logging.getLogger("lb-coupons-api")
log.setLevel(logging.INFO)

log_formatter = logging.Formatter(
    "[%(asctime)s][%(levelname)s] %(filename)s:%(lineno)d | %(message)s"
)

if settings.LOG_TO_CONSOLE:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_formatter)

    root.addHandler(console_handler)


if settings.LOG_TO_FILE:
    file_handler = TimedRotatingFileHandler(
        LOG_FILENAME,
        when="D",
        interval=1,
        backupCount=30,
        encoding=None,
        delay=False,
        utc=True,
        atTime=None,
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(log_formatter)

    root.addHandler(file_handler)

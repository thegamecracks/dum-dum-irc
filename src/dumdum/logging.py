import datetime
import json
import logging
import logging.config
from typing import Any, Literal

from .appdirs import APP_DIRS

BASE_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "root": {
        "level": "DEBUG",
        "handlers": ["stdout", "file"],
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "formatter": "text",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": "",  # Filled in by configure_logging()
            "maxBytes": 5_000_000,
            "backupCount": 3,
        },
    },
    "formatters": {
        "text": {
            "format": "%(message)s",  # Filled in by configure_logging()
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        },
        "json": {
            "()": "dumdum.logging.JSONFormatter",
        },
    },
}

LOG_RECORD_ATTRIBUTES = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",  # cached by formatException()
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "message",
    "module",
    "msecs",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}


def configure_logging(mode: Literal["client", "server"], verbose: int) -> None:
    config = BASE_CONFIG.copy()

    if verbose == 0:
        text_format = "%(levelname)s: %(message)s"
        stdout_level = logging.WARNING
        file_level = logging.INFO
    elif verbose == 1:
        text_format = "%(levelname)s: %(message)s"
        stdout_level = logging.INFO
        file_level = logging.INFO
    else:
        text_format = "%(levelname)s: %(message)-50s (%(name)s#L%(lineno)d)"
        stdout_level = logging.DEBUG
        file_level = logging.DEBUG

    config["formatters"]["text"]["format"] = text_format
    config["handlers"]["stdout"]["level"] = stdout_level
    config["handlers"]["file"]["level"] = file_level

    if mode == "server":
        file_filename = str(APP_DIRS.user_log_path / "dumdum-server.jsonl")
    else:
        file_filename = str(APP_DIRS.user_log_path / "dumdum.jsonl")

    config["handlers"]["file"]["filename"] = file_filename

    logging.config.dictConfig(config)


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = self._prepare_record(record)
        return json.dumps(data, default=str)

    def _prepare_record(self, record: logging.LogRecord) -> dict[str, Any]:
        data = {}

        for k, v in vars(record).items():
            if k not in LOG_RECORD_ATTRIBUTES:
                data[k] = v

        created = datetime.datetime.fromtimestamp(
            record.created,
            tz=datetime.timezone.utc,
        )

        data["created"] = created.isoformat()
        data["message"] = record.getMessage()

        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)

        if record.stack_info:
            data["stack_info"] = self.formatStack(record.stack_info)

        return data

from __future__ import annotations

import logging
import sys

from rich.logging import RichHandler


def configure_logging(level: str = "INFO", *, name: str | None = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level.upper())

    if not any(isinstance(h, RichHandler) for h in logger.handlers):
        handler = RichHandler(rich_tracebacks=True, show_time=True, show_level=True, show_path=False)
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    root = logging.getLogger()
    root.setLevel(level.upper())
    if not root.handlers:
        root.addHandler(logging.StreamHandler(sys.stderr))

    return logger

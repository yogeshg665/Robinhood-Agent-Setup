"""Rich-backed logging configured once for the package."""

from __future__ import annotations

import logging
import os

from rich.logging import RichHandler

_CONFIGURED = False


def _configure(level: str | None = None) -> None:
    global _CONFIGURED
    resolved = (level or os.getenv("LOG_LEVEL") or "INFO").upper()
    logging.basicConfig(
        level=resolved,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
    )
    _CONFIGURED = True


def get_logger(name: str, level: str | None = None) -> logging.Logger:
    """Return a configured logger for ``name``."""
    if not _CONFIGURED:
        _configure(level)
    return logging.getLogger(name)

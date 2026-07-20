"""Application logging helpers."""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from . import __version__


def configure_logging() -> Path | None:
    base = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "OBS Floating Ball"
    try:
        base.mkdir(parents=True, exist_ok=True)
        log_path = base / "app.log"
        handler = RotatingFileHandler(
            log_path,
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
            handlers=[handler],
            force=True,
        )
        logging.info("OBS Floating Ball %s starting", __version__)
        return log_path
    except OSError:
        logging.basicConfig(level=logging.INFO, force=True)
        logging.info("OBS Floating Ball %s starting (console logging)", __version__)
        return None

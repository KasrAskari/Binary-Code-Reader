"""
errorlog.py

Writes unexpected errors to a log file.
A windowed .exe has no console, so without this errors would vanish.
This module knows nothing about Tkinter.
"""

import traceback
from datetime import datetime
from pathlib import Path

from storage import default_config_dir


def log_path() -> Path:
    return default_config_dir() / "error.log"


def log_exception(exc_type, exc_value, exc_tb, path: str | Path | None = None) -> Path | None:
    """Append a traceback to the log file.

    Returns the log path, or None if the file could not be written
    (logging must never raise a second error on top of the first one).
    """
    target = Path(path) if path else log_path()
    text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "a", encoding="utf-8") as file:
            file.write(f"--- {datetime.now():%Y-%m-%d %H:%M:%S} ---\n{text}\n")
    except OSError:
        return None
    return target
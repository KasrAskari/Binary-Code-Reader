"""
storage.py

Small helpers for reading and writing JSON files safely.
This module knows nothing about Tkinter.
"""

import json
import os
from pathlib import Path

APP_FOLDER = "BinaryCodeReader"


def default_config_dir() -> Path:
    """Return the per-user folder where the app keeps its files."""
    appdata = os.environ.get("APPDATA")  # set on Windows
    root = Path(appdata) if appdata else Path.home() / ".config"
    return root / APP_FOLDER


def read_json(path: str | Path):
    """Return the parsed JSON, or None if the file is missing or corrupt."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, ValueError):
        # JSONDecodeError and UnicodeDecodeError are both ValueError subclasses
        return None


def write_json(path: str | Path, data) -> None:
    """Write JSON atomically: temp file first, then replace the real file.

    Raises:
        ValueError: if the file cannot be written.
    """
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except OSError as error:
        raise ValueError(
            f"Cannot save {path.name}: {error.strerror or error}"
        ) from error


def remove_file(path: str | Path) -> None:
    """Delete a file; do nothing if it does not exist.

    Raises:
        ValueError: if the file exists but cannot be deleted.
    """
    try:
        Path(path).unlink(missing_ok=True)
    except OSError as error:
        raise ValueError(
            f"Cannot delete {Path(path).name}: {error.strerror or error}"
        ) from error
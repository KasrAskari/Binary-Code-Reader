"""
settings.py

Loading and saving user settings, with validation.
This module knows nothing about Tkinter.
"""

from pathlib import Path

from converter import DEFAULT_ENCODING, SUPPORTED_ENCODINGS
from storage import read_json, write_json

VALID_THEMES = ("light", "dark")  # must match the keys of THEMES in gui.py

DEFAULT_SETTINGS = {
    "theme": "light",
    "encoding": DEFAULT_ENCODING,
    "remember_history": True,
}


def load_settings(path: str | Path) -> dict:
    """Load settings; any missing or invalid value falls back to its default."""
    settings = dict(DEFAULT_SETTINGS)  # a copy: never mutate the defaults
    data = read_json(path)
    if not isinstance(data, dict):
        return settings

    if data.get("theme") in VALID_THEMES:
        settings["theme"] = data["theme"]
    if data.get("encoding") in SUPPORTED_ENCODINGS:
        settings["encoding"] = data["encoding"]
    if isinstance(data.get("remember_history"), bool):
        settings["remember_history"] = data["remember_history"]
    return settings


def save_settings(path: str | Path, settings: dict) -> None:
    """Save only the known keys.

    Raises:
        ValueError: if the file cannot be written.
    """
    known = {key: settings.get(key, default) for key, default in DEFAULT_SETTINGS.items()}
    write_json(path, known)
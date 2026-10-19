"""
files.py

Reading and writing text files for Binary Code Reader.
This module knows nothing about Tkinter.
"""

import os
from converter import DEFAULT_ENCODING, SUPPORTED_ENCODINGS

MAX_FILE_BYTES = 200_000  # keeps the UI responsive (output is ~9x larger)


def read_text_file(
    path: str,
    encoding: str = DEFAULT_ENCODING,
    max_bytes: int = MAX_FILE_BYTES,
) -> str:
    """Read a text file and return its content with '\\n' line endings.

    Raises:
        ValueError: if the encoding is unsupported, the file cannot be
            opened, is too large, or is not valid text in that encoding.
    """
    if encoding not in SUPPORTED_ENCODINGS:
        raise ValueError(f"Unsupported encoding: {encoding!r}.")

    try:
        size = os.path.getsize(path)
        if size > max_bytes:
            raise ValueError(
                f"File is too large ({size:,} bytes; limit is {max_bytes:,})."
            )
        with open(path, "rb") as file:
            data = file.read()
    except OSError as error:
        raise ValueError(f"Cannot open file: {error.strerror or error}") from error

    # "utf-8-sig" silently drops the BOM that some editors add
    codec = "utf-8-sig" if encoding == "utf-8" else encoding
    try:
        text = data.decode(codec)
    except UnicodeDecodeError as error:
        raise ValueError(f"The file is not valid {encoding.upper()} text.") from error

    return text.replace("\r\n", "\n")


def write_text_file(path: str, text: str) -> None:
    """Write text to a file as UTF-8.

    Raises:
        ValueError: if the file cannot be written.
    """
    try:
        with open(path, "w", encoding="utf-8") as file:
            file.write(text)
    except OSError as error:
        raise ValueError(f"Cannot save file: {error.strerror or error}") from error
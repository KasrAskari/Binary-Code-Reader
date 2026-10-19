"""
converter.py

Core conversion logic for Binary Code Reader.
This module knows nothing about the GUI or the command line.
"""

DEFAULT_ENCODING = "utf-8"
SUPPORTED_ENCODINGS = (
    "utf-8",
    "utf-16-le",
    "utf-16-be",
    "ascii",
    "latin-1",
    "cp1256",
)
BITS_PER_BYTE = 8


def _check_encoding(encoding: str) -> None:
    """Raise ValueError if the encoding is not in the supported list."""
    if encoding not in SUPPORTED_ENCODINGS:
        raise ValueError(
            f"Unsupported encoding: {encoding!r}. "
            f"Supported: {', '.join(SUPPORTED_ENCODINGS)}."
        )


def text_to_binary(text: str, encoding: str = DEFAULT_ENCODING) -> str:
    """Convert text to space-separated 8-bit binary groups.

    Raises:
        TypeError: if text is not a string.
        ValueError: if the encoding is unsupported, the text is empty,
            or the text has characters the encoding cannot represent.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string.")
    _check_encoding(encoding)
    if text == "":
        raise ValueError("Input text is empty.")

    try:
        data = text.encode(encoding)
    except UnicodeEncodeError as error:
        raise ValueError(
            f"The text contains characters that {encoding.upper()} "
            f"cannot represent."
        ) from error
    return " ".join(f"{byte:08b}" for byte in data)


def binary_to_text(binary: str, encoding: str = DEFAULT_ENCODING) -> str:
    """Convert 8-bit binary groups (spaced or not) back to text.

    Raises:
        TypeError: if binary is not a string.
        ValueError: if the encoding is unsupported, the input is empty,
            contains characters other than 0/1, has a length that is not
            a multiple of 8, or does not decode with the given encoding.
    """
    if not isinstance(binary, str):
        raise TypeError("binary must be a string.")
    _check_encoding(encoding)

    # Remove ALL whitespace (spaces, tabs, newlines)
    cleaned = "".join(binary.split())

    if cleaned == "":
        raise ValueError("Input binary is empty.")

    # Only '0' and '1' are allowed
    invalid_chars = sorted(set(cleaned) - {"0", "1"})
    if invalid_chars:
        raise ValueError(
            f"Binary input may only contain 0 and 1 (found: {invalid_chars})."
        )

    if len(cleaned) % BITS_PER_BYTE != 0:
        raise ValueError(
            f"Binary length must be a multiple of {BITS_PER_BYTE} bits "
            f"(got {len(cleaned)} bits)."
        )

    # Split into 8-bit chunks and convert each chunk to a byte
    data = bytes(
        int(cleaned[i : i + BITS_PER_BYTE], 2)
        for i in range(0, len(cleaned), BITS_PER_BYTE)
    )

    # Decode ALL bytes together (multi-byte characters need their neighbors)
    try:
        return data.decode(encoding)
    except UnicodeDecodeError as error:
        raise ValueError(
            f"The bytes are not valid {encoding.upper()} text."
        ) from error


def looks_like_binary(text: str) -> bool:
    """Return True if text looks like valid 8-bit binary input.

    Rule: after removing whitespace the input must be non-empty,
    contain only '0' and '1', and have a length that is a multiple of 8.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string.")

    cleaned = "".join(text.split())
    if cleaned == "":
        return False
    return set(cleaned) <= {"0", "1"} and len(cleaned) % BITS_PER_BYTE == 0


def auto_convert(
    text: str, encoding: str = DEFAULT_ENCODING
) -> tuple[str, str]:
    """Detect the input type and convert it.

    Returns:
        A (mode, result) tuple where mode is "binary_to_text"
        or "text_to_binary".

    Raises:
        TypeError / ValueError: same contract as the two converters.
    """
    if looks_like_binary(text):
        return "binary_to_text", binary_to_text(text, encoding)
    return "text_to_binary", text_to_binary(text, encoding)
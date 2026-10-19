"""
history.py

History of successful conversions, with save/load to a JSON file.
This module knows nothing about Tkinter.
"""

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from converter import SUPPORTED_ENCODINGS
from storage import read_json, write_json

MAX_ENTRIES = 50
PREVIEW_LENGTH = 30
VALID_MODES = ("text_to_binary", "binary_to_text")


@dataclass(frozen=True)
class HistoryEntry:
    mode: str        # "text_to_binary" or "binary_to_text"
    encoding: str
    source: str
    result: str
    time: datetime

    def preview(self) -> str:
        """One-line label for list display."""
        text = " ".join(self.source.split())   # collapse newlines and tabs
        if len(text) > PREVIEW_LENGTH:
            text = text[:PREVIEW_LENGTH] + "…"
        arrow = "T→B" if self.mode == "text_to_binary" else "B→T"
        return f"{self.time:%H:%M:%S}  {arrow}  {text}"

    def to_dict(self) -> dict[str, str]:
        return {
            "mode": self.mode,
            "encoding": self.encoding,
            "source": self.source,
            "result": self.result,
            "time": self.time.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: object) -> "HistoryEntry":
        """Build an entry from untrusted data.

        Raises:
            ValueError: if anything is missing, has the wrong type,
                or has a value the app does not support.
        """
        try:
            entry = cls(
                mode=data["mode"],
                encoding=data["encoding"],
                source=data["source"],
                result=data["result"],
                time=datetime.fromisoformat(data["time"]),  # ValueError if bad
            )
        except (KeyError, TypeError) as error:
            raise ValueError("Malformed history entry.") from error

        texts = (entry.mode, entry.encoding, entry.source, entry.result)
        if not all(isinstance(value, str) for value in texts):
            raise ValueError("History entry fields must be strings.")
        if entry.mode not in VALID_MODES:
            raise ValueError(f"Unknown mode: {entry.mode!r}.")
        if entry.encoding not in SUPPORTED_ENCODINGS:
            raise ValueError(f"Unsupported encoding: {entry.encoding!r}.")
        return entry


class History:
    def __init__(self, max_entries: int = MAX_ENTRIES) -> None:
        self._entries: deque[HistoryEntry] = deque(maxlen=max_entries)

    def add(self, mode: str, encoding: str, source: str, result: str) -> bool:
        """Store an entry. Returns False if it duplicates the latest one."""
        if self._entries:
            last = self._entries[-1]
            if (last.mode, last.encoding, last.source) == (mode, encoding, source):
                return False
        self._entries.append(
            HistoryEntry(mode, encoding, source, result, datetime.now())
        )
        return True

    def entries_newest_first(self) -> list[HistoryEntry]:
        return list(reversed(self._entries))

    def clear(self) -> None:
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)

    # ---------- Persistence ----------

    def save(self, path: str | Path) -> None:
        """Write all entries (oldest first) to a JSON file.

        Raises:
            ValueError: if the file cannot be written.
        """
        write_json(path, [entry.to_dict() for entry in self._entries])

    def load(self, path: str | Path) -> int:
        """Replace the content with entries from a JSON file.

        Malformed entries are skipped. A missing or corrupt file leaves
        the history untouched. Returns the number of valid entries read.
        """
        data = read_json(path)
        if not isinstance(data, list):
            return 0

        valid = []
        for item in data:
            try:
                valid.append(HistoryEntry.from_dict(item))
            except ValueError:
                continue  # skip one bad entry, keep the good ones

        self._entries.clear()
        self._entries.extend(valid)  # maxlen keeps only the newest ones
        return len(valid)
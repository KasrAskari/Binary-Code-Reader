"""tests/test_history.py"""

import tempfile
import unittest
from pathlib import Path

from history import History
from storage import write_json


class TestHistory(unittest.TestCase):
    def test_add_and_order_newest_first(self):
        h = History()
        h.add("text_to_binary", "utf-8", "A", "01000001")
        h.add("text_to_binary", "utf-8", "B", "01000010")
        sources = [e.source for e in h.entries_newest_first()]
        self.assertEqual(sources, ["B", "A"])

    def test_consecutive_duplicate_is_ignored(self):
        h = History()
        self.assertTrue(h.add("text_to_binary", "utf-8", "A", "01000001"))
        self.assertFalse(h.add("text_to_binary", "utf-8", "A", "01000001"))
        self.assertEqual(len(h), 1)

    def test_same_source_with_different_encoding_is_not_duplicate(self):
        h = History()
        h.add("text_to_binary", "utf-8", "A", "01000001")
        self.assertTrue(h.add("text_to_binary", "utf-16-le", "A", "01000001 00000000"))
        self.assertEqual(len(h), 2)

    def test_non_consecutive_repeat_is_kept(self):
        h = History()
        h.add("text_to_binary", "utf-8", "A", "x")
        h.add("text_to_binary", "utf-8", "B", "y")
        self.assertTrue(h.add("text_to_binary", "utf-8", "A", "x"))
        self.assertEqual(len(h), 3)

    def test_max_entries_drops_oldest(self):
        h = History(max_entries=3)
        for i in range(5):
            h.add("text_to_binary", "utf-8", str(i), "x")
        sources = [e.source for e in h.entries_newest_first()]
        self.assertEqual(sources, ["4", "3", "2"])

    def test_clear(self):
        h = History()
        h.add("text_to_binary", "utf-8", "A", "x")
        h.clear()
        self.assertEqual(len(h), 0)

    def test_preview_is_truncated_and_single_line(self):
        h = History()
        h.add("text_to_binary", "utf-8", "line1\nline2 " + "x" * 100, "r")
        preview = h.entries_newest_first()[0].preview()
        self.assertNotIn("\n", preview)
        self.assertTrue(preview.endswith("…"))
        self.assertIn("T→B", preview)


class TestHistoryPersistence(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def test_save_and_load_round_trip(self):
        path = self.dir / "h.json"
        h = History()
        h.add("text_to_binary", "utf-8", "سلام", "x")
        h.add("binary_to_text", "utf-8", "0100", "y")
        h.save(path)

        loaded = History()
        self.assertEqual(loaded.load(path), 2)
        self.assertEqual(loaded.entries_newest_first(), h.entries_newest_first())

    def test_load_missing_file_returns_zero(self):
        self.assertEqual(History().load(self.dir / "nope.json"), 0)

    def test_load_skips_malformed_entries(self):
        path = self.dir / "h.json"
        good = {
            "mode": "text_to_binary",
            "encoding": "utf-8",
            "source": "A",
            "result": "x",
            "time": "2026-10-14T10:00:00",
        }
        bad_items = [
            {"mode": "text_to_binary"},          # missing keys
            {**good, "mode": "nonsense"},        # unknown mode
            {**good, "encoding": "utf-7"},       # unsupported encoding
            {**good, "time": "yesterday"},       # bad timestamp
            {**good, "source": 5},               # wrong type
            "not even a dict",
        ]
        write_json(path, bad_items + [good])

        h = History()
        self.assertEqual(h.load(path), 1)
        self.assertEqual(len(h), 1)

    def test_load_respects_max_entries_and_keeps_newest(self):
        path = self.dir / "h.json"
        h = History()
        for i in range(5):
            h.add("text_to_binary", "utf-8", str(i), "x")
        h.save(path)

        small = History(max_entries=2)
        small.load(path)
        sources = [e.source for e in small.entries_newest_first()]
        self.assertEqual(sources, ["4", "3"])


if __name__ == "__main__":
    unittest.main()
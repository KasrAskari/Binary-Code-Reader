"""tests/test_settings.py"""

import tempfile
import unittest
from pathlib import Path

from settings import DEFAULT_SETTINGS, load_settings, save_settings
from storage import read_json, remove_file, write_json


class _TempDirCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)


class TestStorage(_TempDirCase):
    def test_write_then_read_json(self):
        path = self.dir / "a.json"
        write_json(path, {"name": "سلام", "n": 1})
        self.assertEqual(read_json(path), {"name": "سلام", "n": 1})

    def test_read_missing_file_returns_none(self):
        self.assertIsNone(read_json(self.dir / "nope.json"))

    def test_read_corrupt_file_returns_none(self):
        path = self.dir / "bad.json"
        path.write_text("{not json", encoding="utf-8")
        self.assertIsNone(read_json(path))

    def test_write_creates_missing_folders(self):
        path = self.dir / "sub" / "deeper" / "a.json"
        write_json(path, [1])
        self.assertEqual(read_json(path), [1])

    def test_write_leaves_no_temp_file(self):
        write_json(self.dir / "a.json", {})
        self.assertEqual([p.name for p in self.dir.iterdir()], ["a.json"])

    def test_remove_file_deletes_and_tolerates_missing(self):
        path = self.dir / "a.json"
        write_json(path, {})
        remove_file(path)
        self.assertFalse(path.exists())
        remove_file(path)  # a second call must not raise


class TestSettings(_TempDirCase):
    def test_missing_file_gives_defaults(self):
        self.assertEqual(load_settings(self.dir / "s.json"), DEFAULT_SETTINGS)

    def test_save_then_load(self):
        path = self.dir / "s.json"
        wanted = {"theme": "dark", "encoding": "cp1256", "remember_history": False}
        save_settings(path, wanted)
        self.assertEqual(load_settings(path), wanted)

    def test_invalid_values_fall_back_to_defaults(self):
        path = self.dir / "s.json"
        write_json(
            path,
            {"theme": "neon", "encoding": "utf-7", "remember_history": "yes"},
        )
        self.assertEqual(load_settings(path), DEFAULT_SETTINGS)

    def test_each_key_is_validated_independently(self):
        path = self.dir / "s.json"
        write_json(path, {"theme": "dark", "encoding": "utf-7"})
        loaded = load_settings(path)
        self.assertEqual(loaded["theme"], "dark")                       # kept
        self.assertEqual(loaded["encoding"], DEFAULT_SETTINGS["encoding"])  # reset

    def test_non_dict_json_gives_defaults(self):
        path = self.dir / "s.json"
        write_json(path, [1, 2, 3])
        self.assertEqual(load_settings(path), DEFAULT_SETTINGS)

    def test_unknown_keys_are_not_saved(self):
        path = self.dir / "s.json"
        save_settings(path, {"theme": "dark", "junk": 1})
        self.assertEqual(set(read_json(path)), set(DEFAULT_SETTINGS))


if __name__ == "__main__":
    unittest.main()
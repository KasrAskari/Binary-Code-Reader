"""tests/test_files.py"""

import tempfile
import unittest
from pathlib import Path

from files import read_text_file, write_text_file


class TestReadTextFile(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def _make(self, data: bytes, name: str = "f.txt") -> str:
        path = self.dir / name
        path.write_bytes(data)
        return str(path)

    def test_reads_utf8(self):
        self.assertEqual(read_text_file(self._make(b"Hello")), "Hello")

    def test_reads_persian(self):
        path = self._make("سلام".encode("utf-8"))
        self.assertEqual(read_text_file(path), "سلام")

    def test_strips_utf8_bom(self):
        path = self._make(b"\xef\xbb\xbfHi")
        self.assertEqual(read_text_file(path), "Hi")

    def test_normalizes_windows_line_endings(self):
        path = self._make(b"a\r\nb")
        self.assertEqual(read_text_file(path), "a\nb")

    def test_missing_file_raises(self):
        with self.assertRaisesRegex(ValueError, "Cannot open"):
            read_text_file(str(self.dir / "nope.txt"))

    def test_too_large_raises(self):
        path = self._make(b"x" * 20)
        with self.assertRaisesRegex(ValueError, "too large"):
            read_text_file(path, max_bytes=10)

    def test_wrong_encoding_raises(self):
        path = self._make(b"\xff\xfe\xfa")
        with self.assertRaisesRegex(ValueError, "not valid UTF-8"):
            read_text_file(path)

    def test_unsupported_encoding_raises(self):
        path = self._make(b"Hi")
        with self.assertRaisesRegex(ValueError, "Unsupported encoding"):
            read_text_file(path, "utf-7")

    def test_empty_file_returns_empty_string(self):
        self.assertEqual(read_text_file(self._make(b"")), "")


class TestWriteTextFile(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def test_write_then_read_back(self):
        path = str(self.dir / "out.txt")
        write_text_file(path, "سلام\nHi 😀")
        self.assertEqual(read_text_file(path), "سلام\nHi 😀")

    def test_missing_folder_raises(self):
        path = str(self.dir / "no_such_folder" / "out.txt")
        with self.assertRaisesRegex(ValueError, "Cannot save"):
            write_text_file(path, "x")


if __name__ == "__main__":
    unittest.main()
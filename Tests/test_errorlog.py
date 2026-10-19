"""tests/test_errorlog.py"""

import sys
import tempfile
import unittest
from pathlib import Path

from errorlog import log_exception


def _capture(message: str):
    """Raise and catch an error, returning sys.exc_info()."""
    try:
        raise RuntimeError(message)
    except RuntimeError:
        return sys.exc_info()


class TestLogException(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def test_writes_traceback_to_file(self):
        path = self.dir / "error.log"
        result = log_exception(*_capture("boom"), path=path)
        self.assertEqual(result, path)
        content = path.read_text(encoding="utf-8")
        self.assertIn("RuntimeError: boom", content)

    def test_appends_instead_of_overwriting(self):
        path = self.dir / "error.log"
        log_exception(*_capture("first"), path=path)
        log_exception(*_capture("second"), path=path)
        content = path.read_text(encoding="utf-8")
        self.assertIn("first", content)
        self.assertIn("second", content)

    def test_returns_none_when_file_cannot_be_written(self):
        # A directory cannot be opened as a file, so the write fails
        self.assertIsNone(log_exception(*_capture("x"), path=self.dir))


if __name__ == "__main__":
    unittest.main()
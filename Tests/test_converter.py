"""
tests/test_converter.py

Automated tests for converter.py (Phase 3).
Run from the project root with: python -m unittest -v
"""

import unittest

from converter import (
    SUPPORTED_ENCODINGS,
    auto_convert,
    binary_to_text,
    looks_like_binary,
    text_to_binary,
)


class TestTextToBinary(unittest.TestCase):
    """Text -> Binary: known values, UTF-8 behavior, and errors."""

    def test_simple_english(self):
        self.assertEqual(
            text_to_binary("Hello"),
            "01001000 01100101 01101100 01101100 01101111",
        )

    def test_single_letter(self):
        self.assertEqual(text_to_binary("A"), "01000001")

    def test_digits_are_characters_not_numbers(self):
        # The character "1" is ASCII 49, not the number 1
        self.assertEqual(text_to_binary("123"), "00110001 00110010 00110011")

    def test_space_is_a_valid_character(self):
        self.assertEqual(text_to_binary(" "), "00100000")

    def test_special_characters(self):
        self.assertEqual(text_to_binary("@#$"), "01000000 00100011 00100100")

    def test_persian_letter_uses_two_bytes(self):
        self.assertEqual(text_to_binary("س"), "11011000 10110011")

    def test_emoji_uses_four_bytes(self):
        self.assertEqual(
            text_to_binary("😀"),
            "11110000 10011111 10011000 10000000",
        )

    def test_empty_text_raises_value_error(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            text_to_binary("")

    def test_non_string_raises_type_error(self):
        for value in (None, 123, b"Hi"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    text_to_binary(value)

    def test_lone_surrogate_raises_value_error(self):
        # A lone surrogate cannot be encoded to UTF-8
        with self.assertRaises(ValueError):
            text_to_binary("\ud800")


class TestBinaryToText(unittest.TestCase):
    """Binary -> Text: input formats, UTF-8 decoding, and validation."""

    def test_simple_english(self):
        self.assertEqual(
            binary_to_text("01001000 01100101 01101100 01101100 01101111"),
            "Hello",
        )

    def test_input_without_spaces(self):
        self.assertEqual(binary_to_text("0100100001100101"), "He")

    def test_mixed_whitespace_is_ignored(self):
        self.assertEqual(
            binary_to_text("01001000\n01100101\t01101100  01101100 01101111"),
            "Hello",
        )

    def test_persian_letter(self):
        self.assertEqual(binary_to_text("11011000 10110011"), "س")

    def test_emoji(self):
        self.assertEqual(
            binary_to_text("11110000 10011111 10011000 10000000"),
            "😀",
        )

    def test_empty_input_raises(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            binary_to_text("")

    def test_whitespace_only_input_raises(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            binary_to_text("   \n\t ")

    def test_invalid_characters_raise(self):
        with self.assertRaisesRegex(ValueError, "only contain 0 and 1"):
            binary_to_text("0100 1000 2")

    def test_persian_digits_are_rejected(self):
        # int("۰۱۰۰۱۰۰۰", 2) works in Python, so we must block it ourselves
        with self.assertRaisesRegex(ValueError, "only contain 0 and 1"):
            binary_to_text("۰۱۰۰۱۰۰۰")

    def test_wrong_length_raises(self):
        with self.assertRaisesRegex(ValueError, "multiple of 8"):
            binary_to_text("0100100")

    def test_truncated_multibyte_character_raises(self):
        # Only the first byte of a 2-byte Persian letter
        with self.assertRaisesRegex(ValueError, "not valid UTF-8"):
            binary_to_text("11011000")

    def test_invalid_utf8_byte_raises(self):
        # 0xFF never appears in valid UTF-8
        with self.assertRaisesRegex(ValueError, "not valid UTF-8"):
            binary_to_text("11111111")

    def test_non_string_raises_type_error(self):
        for value in (None, 123, b"01001000"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    binary_to_text(value)


class TestRoundTrip(unittest.TestCase):
    """The core promise: binary_to_text(text_to_binary(x)) == x."""

    def test_round_trip_samples(self):
        samples = [
            "Hello",
            "123",
            " ",
            "Hi there!",
            "line1\nline2",
            "سلام",
            "سلام، حالت چطوره؟",
            "Hello سلام 😀",
        ]
        for text in samples:
            with self.subTest(text=text):
                self.assertEqual(binary_to_text(text_to_binary(text)), text)

    def test_round_trip_every_ascii_character(self):
        for code in range(128):
            char = chr(code)
            with self.subTest(code=code):
                self.assertEqual(binary_to_text(text_to_binary(char)), char)

# Update the import at the top of the file:
from converter import (
    auto_convert,
    binary_to_text,
    looks_like_binary,
    text_to_binary,
)

class TestLooksLikeBinary(unittest.TestCase):
    def test_valid_binary_with_spaces(self):
        self.assertTrue(looks_like_binary("01001000 01100101"))

    def test_valid_binary_without_spaces(self):
        self.assertTrue(looks_like_binary("0100100001100101"))

    def test_wrong_length_is_not_binary(self):
        self.assertFalse(looks_like_binary("1010"))

    def test_text_is_not_binary(self):
        self.assertFalse(looks_like_binary("Hello"))

    def test_digits_other_than_0_1_are_not_binary(self):
        self.assertFalse(looks_like_binary("12345678"))

    def test_persian_digits_are_not_binary(self):
        self.assertFalse(looks_like_binary("۰۱۰۰۱۰۰۰"))

    def test_empty_and_whitespace_are_not_binary(self):
        for value in ("", "   ", "\n\t"):
            with self.subTest(value=value):
                self.assertFalse(looks_like_binary(value))

    def test_non_string_raises_type_error(self):
        with self.assertRaises(TypeError):
            looks_like_binary(None)


class TestAutoConvert(unittest.TestCase):
    def test_detects_binary(self):
        self.assertEqual(
            auto_convert("01001000 01100101"), ("binary_to_text", "He")
        )

    def test_detects_text(self):
        self.assertEqual(
            auto_convert("Hi"), ("text_to_binary", "01001000 01101001")
        )

    def test_persian_text_is_detected_as_text(self):
        mode, _ = auto_convert("سلام")
        self.assertEqual(mode, "text_to_binary")

    def test_known_ambiguity_binary_looking_text_is_treated_as_binary(self):
        # Documented trade-off: "01000001" is read as binary for "A"
        self.assertEqual(auto_convert("01000001"), ("binary_to_text", "A"))

    def test_empty_input_raises(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            auto_convert("")

    def test_binary_that_is_invalid_utf8_raises(self):
        # Looks like binary, so it goes down the binary path and fails there
        with self.assertRaisesRegex(ValueError, "not valid UTF-8"):
            auto_convert("11111111")
            
class TestEncodings(unittest.TestCase):
    def test_ascii_english(self):
        self.assertEqual(text_to_binary("A", "ascii"), "01000001")

    def test_ascii_rejects_persian(self):
        with self.assertRaisesRegex(ValueError, "cannot represent"):
            text_to_binary("س", "ascii")

    def test_latin1_vs_utf8_for_accented_letter(self):
        self.assertEqual(text_to_binary("é", "latin-1"), "11101001")
        self.assertEqual(text_to_binary("é", "utf-8"), "11000011 10101001")

    def test_cp1256_encodes_persian_letter_as_one_byte(self):
        binary = text_to_binary("س", "cp1256")
        self.assertEqual(len(binary), 8)
        self.assertEqual(binary_to_text(binary, "cp1256"), "س")

    def test_utf16_le_and_be_byte_order(self):
        self.assertEqual(text_to_binary("A", "utf-16-le"), "01000001 00000000")
        self.assertEqual(text_to_binary("A", "utf-16-be"), "00000000 01000001")

    def test_utf16_odd_number_of_bytes_raises(self):
        # UTF-16 needs pairs of bytes; a single byte is incomplete
        with self.assertRaisesRegex(ValueError, "not valid UTF-16-LE"):
            binary_to_text("01000001", "utf-16-le")

    def test_latin1_accepts_any_byte(self):
        # Every byte value maps to some character in latin-1
        self.assertEqual(binary_to_text("11111111", "latin-1"), "\xff")

    def test_unsupported_encoding_raises(self):
        for func, value in ((text_to_binary, "A"), (binary_to_text, "01000001")):
            with self.subTest(func=func.__name__):
                with self.assertRaisesRegex(ValueError, "Unsupported encoding"):
                    func(value, "utf-7")

    def test_round_trip_all_supported_encodings(self):
        for encoding in SUPPORTED_ENCODINGS:
            with self.subTest(encoding=encoding):
                binary = text_to_binary("Hello", encoding)
                self.assertEqual(binary_to_text(binary, encoding), "Hello")

    def test_auto_convert_passes_encoding_through(self):
        self.assertEqual(
            auto_convert("A", "utf-16-be"),
            ("text_to_binary", "00000000 01000001"),
        )

if __name__ == "__main__":
    unittest.main()
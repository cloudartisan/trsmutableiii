import unittest
import sys
import os

# Add the project root to the Python path when running directly
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
from wargames.utils import wrap_text


class TestTextWrapping(unittest.TestCase):
    """Test suite for text wrapping functionality using unittest."""

    def test_wrap_text_multiple_lines(self):
        """Test wrapping text into multiple lines."""
        text = "This is a test of the wrapping function"
        wrapped_lines = wrap_text(text, 10)
        self.assertEqual(wrapped_lines, [
            "This is a",
            "test of",
            "the",
            "wrapping",
            "function"
        ])

    def test_wrap_text_single_line(self):
        """Test text that fits on a single line."""
        text = "This is a test of the wrapping function"
        wrapped_lines = wrap_text(text, 100)
        self.assertEqual(wrapped_lines, [text])

    def test_wrap_text_long_words(self):
        """Test text with very long words."""
        text = "This is a test of the wrapping function withaverylongword"
        wrapped_lines = wrap_text(text, 10)
        self.assertEqual(wrapped_lines, [
            "This is a",
            "test of",
            "the",
            "wrapping",
            "function",
            "withaverylongword"
        ])

    def test_wrap_text_empty_string(self):
        """Test wrapping an empty string."""
        text = ""
        wrapped_lines = wrap_text(text, 10)
        self.assertEqual(wrapped_lines, [""])

    def test_wrap_text_single_word(self):
        """Test wrapping a single word that fits."""
        text = "word"
        wrapped_lines = wrap_text(text, 10)
        self.assertEqual(wrapped_lines, [text])

    def test_wrap_text_single_word_long(self):
        """Test wrapping a single long word."""
        text = "averylongword"
        wrapped_lines = wrap_text(text, 10)
        self.assertEqual(wrapped_lines, [text])


if __name__ == "__main__":
    unittest.main()
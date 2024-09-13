import pytest
from unittest import mock

from .utils import wrap_text

def test_wrap_text():
    text = "This is a test of the wrapping function"
    wrapped_lines = wrap_text(text, 10)
    assert wrapped_lines == [
        "This is a",
        "test of",
        "the",
        "wrapping",
        "function"
    ]

def test_wrap_text_single_line():
    text = "This is a test of the wrapping function"
    wrapped_lines = wrap_text(text, 100)
    assert wrapped_lines == [text]

def test_wrap_text_long_words():
    text = "This is a test of the wrapping function withaverylongword"
    wrapped_lines = wrap_text(text, 10)
    assert wrapped_lines == [
        "This is a",
        "test of",
        "the",
        "wrapping",
        "function",
        "withaverylongword"
    ]

def test_wrap_text_empty_string():
    text = ""
    wrapped_lines = wrap_text(text, 10)
    assert wrapped_lines == [""]

def test_wrap_text_single_word():
    text = "word"
    wrapped_lines = wrap_text(text, 10)
    assert wrapped_lines == [text]

def test_wrap_text_single_word_long():
    text = "averylongword"
    wrapped_lines = wrap_text(text, 10)
    assert wrapped_lines == [text]
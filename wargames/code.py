#!/usr/bin/env python3

import board
import displayio
import gc
import terminalio
from adafruit_display_text import label
from adafruit_st7789 import ST7789
import time
import json

from .utils import wrap_text

# Constants for display configuration
LEFT_MARGIN = 10
RIGHT_MARGIN = 10
TOP_MARGIN = 20
FONT_SCALE = 1
CHAR_WIDTH = 6  # Adjust for your font size
LINE_HEIGHT = 15  # Adjust for your font size
DEFAULT_TEXT_COLOUR = (0, 255, 255)  # Default colour (RGB format)

# Physical display configuration to be initialised
SPI = board.SPI()
TFT_CS = board.D5  # Chip select pin
TFT_DC = board.D16  # Data/command pin
TFT_RESET = board.D9  # Reset pin

DEFAULT_DEBUG_DELAY=1
DEFAULT_SCREEN_DELAY=4
DEFAULT_CHAR_DELAY=0.025
DEFAULT_LOWER_DELAY=0.25
DEFAULT_UPPER_DELAY=0.005


def debug_print(*lines, delay=DEFAULT_DEBUG_DELAY):
    """Print debug messages with an optional delay"""
    for line in lines:
        print(line)
        time.sleep(delay)


def debug_board():
    """Print debug information about the board"""
    debug_print(f"Board name: {board.board_id}", delay=10)


def clear_display(display):
    debug_print("Clearing display...")
    splash = displayio.Group()
    display.show(splash)
    gc.collect()  # Explicitly collect garbage after clearing display
    return splash


def load_screens(file_path):
    """Load screens from a JSON file"""
    with open(file_path, 'r') as file:
        screens = json.load(file)
    return screens


def display_line_with_typing(splash, text, x, y, scale, colour, upper_delay, lower_delay):
    """Display a single line with a typing effect"""
    text_area = label.Label(terminalio.FONT, text="", x=x, y=y, scale=scale, color=colour)
    splash.append(text_area)

    for char in text:
        char_delay = DEFAULT_CHAR_DELAY
        if char.islower():
            char_delay = lower_delay
        elif char.isupper():
            char_delay = upper_delay

        text_area.text += char
        time.sleep(char_delay)

    return y + LINE_HEIGHT  # Advance to the next line position


def format_and_display_line(display, splash, left_text, centre_text, right_text, y, scale, colour, upper_delay, lower_delay):
    """Format and display a line with left, centre, and right alignment"""
    total_chars = (display.width - LEFT_MARGIN - RIGHT_MARGIN) // CHAR_WIDTH
    left_lines = wrap_text(left_text, total_chars)
    centre_lines = wrap_text(centre_text, total_chars)
    right_lines = wrap_text(right_text, total_chars)

    max_lines = max(len(left_lines), len(centre_lines), len(right_lines))

    for i in range(max_lines):
        left_part = left_lines[i] if i < len(left_lines) else ""
        centre_part = centre_lines[i] if i < len(centre_lines) else ""
        right_part = right_lines[i] if i < len(right_lines) else ""

        if centre_part:
            centre_start = (total_chars - len(centre_part)) // 2
            left_pad = centre_start - len(left_part)
            right_pad = total_chars - (centre_start + len(centre_part) + len(right_part))
        else:
            left_pad = 0
            right_pad = total_chars - len(left_part) - len(right_part)

        padded_left_text = left_part + ' ' * left_pad
        padded_right_text = ' ' * right_pad + right_part
        full_text = padded_left_text + centre_part + padded_right_text

        y = display_line_with_typing(splash, full_text, LEFT_MARGIN, y, scale, colour, upper_delay, lower_delay)

    return y


def display_screen_with_typing(display, screen):
    """Display all lines of a screen with a typing effect"""
    debug_print("Displaying screen with typing effect")
    splash = clear_display(display)

    lines = screen["lines"]
    scale = screen.get("scale", FONT_SCALE)
    colour = tuple(screen.get("colour", DEFAULT_TEXT_COLOUR))
    upper_delay = screen.get("upper_delay", DEFAULT_UPPER_DELAY)
    lower_delay = screen.get("lower_delay", DEFAULT_LOWER_DELAY)
    line_delays = screen.get("line_delays", {})
    y = TOP_MARGIN

    for idx, (left_text, centre_text, right_text, *delay) in enumerate(lines):
        debug_print(f"Displaying line {idx}: {left_text}, {centre_text}, {right_text}")
        y = format_and_display_line(display, splash, left_text, centre_text, right_text, y, scale, colour, upper_delay, lower_delay)
        if delay:
            time.sleep(delay[0])
        elif idx in line_delays:
            time.sleep(line_delays[idx])

    debug_print("Displayed all lines of the screen with typing effect")


def display_screens(display):
    """
    Loop through every screen, displaying them with typing effect, delay
    after each screen, then clear the display, repeat ad infinitum.
    """
    screens = load_screens('./screens.json')
    while True:
        for screen in screens:
            try:
                display_screen_with_typing(display, screen)
            except Exception as e:
                debug_print(f"Error displaying screen: {e}", delay=5)
            time.sleep(screen.get("delay", DEFAULT_SCREEN_DELAY))


def initialise_display():
    try:
        displayio.release_displays()
        display_bus = displayio.FourWire(
            SPI,
            command=TFT_DC,
            chip_select=TFT_CS,
            reset=TFT_RESET
        )
        display = ST7789(
            display_bus,
            width=280,
            height=240,
            rowstart=20,
            rotation=270
        )
        debug_print("Display initialised successfully")
    except Exception as e:
        debug_print(f"Error initialising display: {e}", delay=5)
        raise e

    # Display properties
    debug_print(
        f"Display width: {display.width}",
        f"Display height: {display.height}",
        f"Display rotation: {display.rotation}"
    )
    return display


def main():
    debug_board()
    display = initialise_display()
    display_screens(display)


if __name__ == "__main__":
    main()
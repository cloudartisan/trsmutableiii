#!/usr/bin/env python3

import board
import displayio
import terminalio
import time
import random
from adafruit_display_text import label
from adafruit_st7789 import ST7789

# Constants for display configuration
LEFT_MARGIN = 10
RIGHT_MARGIN = 10
TOP_MARGIN = 20
FONT_SCALE = 1
CHAR_WIDTH = 6  # Width of character in pixels
LINE_HEIGHT = 15  # Height of line in pixels
DELAY = 0.2  # Delay between generations

# Conway's Game of Life grid dimensions
GRID_WIDTH = 40  # Characters per row
GRID_HEIGHT = 14  # Number of rows

# Cell representation characters
LIVE_CELL = '█'  # Full block character
DEAD_CELL = ' '  # Space character

# Physical display configuration
SPI = board.SPI()
TFT_CS = board.D5  # Chip select pin
TFT_DC = board.D16  # Data/command pin
TFT_RESET = board.D9  # Reset pin

# Patterns to initialize the grid
PATTERNS = {
    'glider': [
        (1, 0), (2, 1), (0, 2), (1, 2), (2, 2)
    ],
    'blinker': [
        (1, 0), (1, 1), (1, 2)
    ],
    'glider_gun': [
        (0, 4), (0, 5), (1, 4), (1, 5),  # Block
        (10, 4), (10, 5), (10, 6), (11, 3), (11, 7), (12, 2), (12, 8), (13, 2), (13, 8), (14, 5), (15, 3), (15, 7), (16, 4), (16, 5), (16, 6), (17, 5),  # Left gun part
        (20, 2), (20, 3), (20, 4), (21, 2), (21, 3), (21, 4), (22, 1), (22, 5), (24, 0), (24, 1), (24, 5), (24, 6),  # Right gun part
        (34, 2), (34, 3), (35, 2), (35, 3)  # Block
    ],
    'pulsar': [
        (2, 0), (3, 0), (4, 0), (8, 0), (9, 0), (10, 0),
        (0, 2), (5, 2), (7, 2), (12, 2),
        (0, 3), (5, 3), (7, 3), (12, 3),
        (0, 4), (5, 4), (7, 4), (12, 4),
        (2, 5), (3, 5), (4, 5), (8, 5), (9, 5), (10, 5),
        (2, 7), (3, 7), (4, 7), (8, 7), (9, 7), (10, 7),
        (0, 8), (5, 8), (7, 8), (12, 8),
        (0, 9), (5, 9), (7, 9), (12, 9),
        (0, 10), (5, 10), (7, 10), (12, 10),
        (2, 12), (3, 12), (4, 12), (8, 12), (9, 12), (10, 12)
    ]
}

# Random pattern will be generated in main() to avoid issues with the simulator

# Current pattern to use - can be changed to any pattern in PATTERNS
CURRENT_PATTERN = 'glider_gun'


def debug_print(*lines, delay=1):
    """Print debug messages with an optional delay"""
    for line in lines:
        print(line)
        time.sleep(delay)


def initialise_display():
    """Initialize the display"""
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
        debug_print("Display initialized successfully")
    except Exception as e:
        debug_print(f"Error initializing display: {e}", delay=5)
        raise e

    debug_print(
        f"Display width: {display.width}",
        f"Display height: {display.height}",
        f"Display rotation: {display.rotation}"
    )
    return display


def create_grid():
    """Create a new grid initialized with dead cells"""
    return [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]


def initialize_grid(grid, pattern_name):
    """Initialize the grid with a specific pattern"""
    # Start with all dead cells
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            grid[y][x] = 0
    
    # Set live cells according to the pattern
    if pattern_name in PATTERNS:
        for x, y in PATTERNS[pattern_name]:
            if 0 <= y < GRID_HEIGHT and 0 <= x < GRID_WIDTH:
                grid[y][x] = 1
    
    return grid


def count_neighbors(grid, x, y):
    """Count the number of live neighbors for a cell"""
    count = 0
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            if dx == 0 and dy == 0:  # Skip the cell itself
                continue
            nx, ny = x + dx, y + dy
            # Wrap around the edges (toroidal grid)
            nx = nx % GRID_WIDTH
            ny = ny % GRID_HEIGHT
            count += grid[ny][nx]
    return count


def update_grid(grid):
    """Apply Conway's Game of Life rules to update the grid"""
    new_grid = create_grid()
    
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            neighbors = count_neighbors(grid, x, y)
            if grid[y][x] == 1:  # Cell is alive
                # Cell stays alive if it has 2 or 3 live neighbors
                if neighbors == 2 or neighbors == 3:
                    new_grid[y][x] = 1
                else:  # Cell dies
                    new_grid[y][x] = 0
            else:  # Cell is dead
                # Cell becomes alive if it has exactly 3 live neighbors
                if neighbors == 3:
                    new_grid[y][x] = 1
                else:  # Cell stays dead
                    new_grid[y][x] = 0
    
    return new_grid


def display_grid(display, grid, generation_count=0):
    """Display the grid on the screen"""
    splash = displayio.Group()
    display.show(splash)
    
    for y in range(GRID_HEIGHT):
        line = ''
        for x in range(GRID_WIDTH):
            if grid[y][x] == 1:
                line += LIVE_CELL
            else:
                line += DEAD_CELL
        
        text_area = label.Label(
            terminalio.FONT,
            text=line,
            x=LEFT_MARGIN,
            y=TOP_MARGIN + y * LINE_HEIGHT,
            color=0x00FF00  # Green color for cells
        )
        splash.append(text_area)
    
    # Add generation counter and name at the bottom
    info_text = label.Label(
        terminalio.FONT,
        text=f"Conway - {CURRENT_PATTERN} - Gen {generation_count}",
        x=LEFT_MARGIN,
        y=TOP_MARGIN + (GRID_HEIGHT + 1) * LINE_HEIGHT,
        color=0xFFFFFF  # White color for text
    )
    splash.append(info_text)


def main():
    # Use the global CURRENT_PATTERN variable
    global CURRENT_PATTERN
    
    # Add a random pattern dynamically
    if 'random' not in PATTERNS:
        PATTERNS['random'] = []
        for _ in range(50):  # Fewer random cells for better visibility
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            PATTERNS['random'].append((x, y))
    
    display = initialise_display()
    grid = create_grid()
    grid = initialize_grid(grid, CURRENT_PATTERN)
    generation = 0
    
    # Fixed number of generations per pattern for demo purposes
    max_generations = 50
    
    while True:
        display_grid(display, grid, generation)
        time.sleep(DELAY)
        grid = update_grid(grid)
        generation += 1
        
        # Every max_generations, restart with a different pattern
        if generation >= max_generations:
            generation = 0
            patterns = list(PATTERNS.keys())
            current_index = patterns.index(CURRENT_PATTERN)
            next_index = (current_index + 1) % len(patterns)
            CURRENT_PATTERN = patterns[next_index]
            grid = initialize_grid(grid, CURRENT_PATTERN)


if __name__ == "__main__":
    main()

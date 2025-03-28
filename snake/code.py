#!/usr/bin/env python3

import board
import displayio
import terminalio
import time
import random
from adafruit_display_text import label
from adafruit_st7789 import ST7789

# Constants for display configuration
DISPLAY_WIDTH = 280
DISPLAY_HEIGHT = 240
LEFT_MARGIN = 10
RIGHT_MARGIN = 10
TOP_MARGIN = 20
BOTTOM_MARGIN = 10

# Special flag to handle double-width horizontal rendering
HORIZONTAL_DOUBLE_WIDTH = True  # When true, horizontal snake segments use two characters

# Game constants
GRID_WIDTH = 32  # Width of play area in characters
GRID_HEIGHT = 16  # Height of play area in characters
LOGICAL_GRID_WIDTH = GRID_WIDTH // 2 if HORIZONTAL_DOUBLE_WIDTH else GRID_WIDTH  # Logical width for game logic
GAME_SPEED = 0.15  # Delay between frames (lower is faster)
SNAKE_SPEEDUP_FACTOR = 0.98  # Speed increases by this factor when snake eats (less drastic)
MIN_GAME_SPEED = 0.05  # Don't allow the game to get faster than this
COLOR_SNAKE = 0x00FF00  # Green
COLOR_FOOD = 0xFF0000  # Red
COLOR_BORDER = 0xFFFFFF  # White

# Game characters
SNAKE_HEAD_CHAR = '█'  # Snake head character (full block)
SNAKE_BODY_CHAR = '█'  # Snake body character (full block)
FOOD_CHAR = '●'        # Food character
EMPTY_CHAR = ' '       # Empty space character
BORDER_CHAR = '░'      # Border character (lighter pattern)


# Physical display configuration
SPI = board.SPI()
TFT_CS = board.D5  # Chip select pin
TFT_DC = board.D16  # Data/command pin
TFT_RESET = board.D9  # Reset pin

# Directions (dx, dy)
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

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
            width=DISPLAY_WIDTH,
            height=DISPLAY_HEIGHT,
            rowstart=20,
            rotation=270
        )
        debug_print("Display initialized successfully")
    except Exception as e:
        debug_print(f"Error initializing display: {e}", delay=5)
        raise e

    return display

class SnakeGame:
    """Snake game implementation"""
    
    def __init__(self, display):
        self.display = display
        self.game_over = False
        self.score = 0
        self.high_score = 0
        self.speed = GAME_SPEED
        self.grid = [[EMPTY_CHAR for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        
        # Initialize snake in the middle of the screen
        # Use logical grid width for snake positions
        self.snake = [(LOGICAL_GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = random.choice([UP, DOWN, LEFT, RIGHT])
        
        # Create initial food
        self.food_pos = None
        self.create_food()
        
        # Draw initial border
        self.draw_border()
        
        # Counter for frames since game started (for mistake probability calculation)
        self.frames = 0
        
    def draw_border(self):
        """Draw the game border"""
        # Top and bottom borders
        for x in range(GRID_WIDTH):
            self.grid[0][x] = BORDER_CHAR
            self.grid[GRID_HEIGHT-1][x] = BORDER_CHAR
        
        # Left and right borders
        for y in range(GRID_HEIGHT):
            self.grid[y][0] = BORDER_CHAR
            self.grid[y][GRID_WIDTH-1] = BORDER_CHAR
    
    def create_food(self):
        """Create food at a random empty location"""
        empty_cells = []
        for y in range(1, GRID_HEIGHT-1):
            for x in range(1, LOGICAL_GRID_WIDTH-1):  # Use logical grid width
                # Check if cell is empty and not occupied by the snake
                if (x, y) not in self.snake:
                    empty_cells.append((x, y))
        
        if empty_cells:
            self.food_pos = random.choice(empty_cells)
    
    def update_grid(self):
        """Update the grid based on current game state"""
        # Clear the grid (except border)
        for y in range(1, GRID_HEIGHT-1):
            for x in range(1, GRID_WIDTH-1):
                self.grid[y][x] = EMPTY_CHAR
        
        # Place food - just use one cell for food to avoid double appearance
        if self.food_pos:
            food_x, food_y = self.food_pos
            if HORIZONTAL_DOUBLE_WIDTH:
                # Convert logical x to display x (multiply by 2)
                display_x = food_x * 2
                # Place food in a single cell for better appearance
                if 0 <= food_y < GRID_HEIGHT and 0 <= display_x < GRID_WIDTH-1:
                    self.grid[food_y][display_x] = FOOD_CHAR
            else:
                # Normal placement for non-double width
                if 0 <= food_y < GRID_HEIGHT and 0 <= food_x < GRID_WIDTH:
                    self.grid[food_y][food_x] = FOOD_CHAR
        
        # Place snake
        for i, (x, y) in enumerate(self.snake):
            if 0 <= y < GRID_HEIGHT:
                if HORIZONTAL_DOUBLE_WIDTH:
                    # Check if this segment is moving horizontally
                    is_horizontal = False
                    if i < len(self.snake) - 1:
                        next_x, next_y = self.snake[i+1]
                        is_horizontal = (y == next_y)  # Same y means horizontal movement
                    
                    # Convert logical x to display x (multiply by 2)
                    display_x = x * 2
                    
                    if 0 <= display_x < GRID_WIDTH-1:  # Ensure we don't go out of bounds
                        # Place the snake segment as two consecutive blocks for horizontal
                        self.grid[y][display_x] = SNAKE_HEAD_CHAR if i == 0 else SNAKE_BODY_CHAR
                        self.grid[y][display_x+1] = SNAKE_HEAD_CHAR if i == 0 else SNAKE_BODY_CHAR
                else:
                    # Normal placement for non-double width
                    if 0 <= x < GRID_WIDTH:
                        self.grid[y][x] = SNAKE_HEAD_CHAR if i == 0 else SNAKE_BODY_CHAR
    
    def move_snake(self):
        """Move the snake in the current direction"""
        self.frames += 1  # Increment frame counter
        
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)
        new_x, new_y = new_head
        
        # Calculate mistake probability based on snake length and time
        # Longer snake and longer playtime = slightly higher chance of mistake
        # But still very low to ensure good gameplay for a long time
        mistake_probability = 0
        if len(self.snake) > 15:  # Only start making mistakes when snake is longer (reduced early teleporting)
            # Start introducing mistakes after snake length 15
            # Very small probability that increases slightly with length
            length_factor = min(0.002, 0.00005 * (len(self.snake) - 15))  # Reduced probability
            time_factor = min(0.0005, 0.000005 * self.frames)  # Reduced time factor
            mistake_probability = length_factor + time_factor
        
        # Check for collisions - use logical grid width for x boundaries
        wall_collision = (new_x <= 0 or new_x >= LOGICAL_GRID_WIDTH-1 or 
                         new_y <= 0 or new_y >= GRID_HEIGHT-1)
        self_collision = new_head in self.snake
        
        # Decide whether to avoid or allow collision
        if (wall_collision or self_collision):
            # Small chance to make a mistake when snake is long
            # Only allow mistakes at reasonable intervals to avoid early teleportation impression
            if random.random() < mistake_probability and self.frames > 100:
                # Make a deliberate mistake - allow collision to happen
                self.handle_collision()
                return
            else:
                # No mistake - try to avoid collision
                if wall_collision:
                    self.avoid_wall()
                    return
                elif self_collision:
                    self.avoid_self()
                    return
        
        # Move the snake
        self.snake.insert(0, new_head)
        
        # Check if snake ate food
        if new_head == self.food_pos:
            # Snake ate food, create new food and don't remove tail
            self.score += 1
            if self.score > self.high_score:
                self.high_score = self.score
            # Speed up the game but don't go below the minimum speed
            self.speed = max(MIN_GAME_SPEED, self.speed * SNAKE_SPEEDUP_FACTOR)
            self.create_food()
        else:
            # Snake didn't eat food, remove tail
            self.snake.pop()
    
    def handle_collision(self):
        """Handle collision - display collision and reset game"""
        self.game_over = True
        
        # Update grid to show final state
        self.update_grid()
        
        # Show collision state
        splash = displayio.Group()
        self.display.show(splash)
        
        # Display game grid with collision
        for y, row in enumerate(self.grid):
            line = ''.join(row)
            row_color = COLOR_SNAKE
            text_area = label.Label(
                terminalio.FONT,
                text=line,
                x=LEFT_MARGIN + 20,  # Match the extra margin used in display_game
                y=TOP_MARGIN + y * 14,
                color=row_color
            )
            splash.append(text_area)
        
        # Display game over message
        game_over_text = "GAME OVER"
        game_over_area = label.Label(
            terminalio.FONT,
            text=game_over_text,
            x=LEFT_MARGIN + 20 + (GRID_WIDTH // 2) * 6 - 30,  # Center on screen
            y=TOP_MARGIN + GRID_HEIGHT * 14 + 10,
            color=0xFF0000  # Red color
        )
        splash.append(game_over_area)
        
        # Display score
        score_text = f"Score: {self.score} - High: {self.high_score}"
        score_area = label.Label(
            terminalio.FONT,
            text=score_text,
            x=LEFT_MARGIN + 20,  # Match the extra margin
            y=TOP_MARGIN + GRID_HEIGHT * 14 + 30,
            color=COLOR_BORDER
        )
        splash.append(score_area)
        
        # Pause to show collision
        time.sleep(2)
        
        # Reset game state
        self.reset_game()
    
    def avoid_wall(self):
        """AI logic to avoid hitting walls"""
        head_x, head_y = self.snake[0]
        possible_directions = [UP, DOWN, LEFT, RIGHT]
        
        # Remove directions that would hit walls
        if head_y <= 1:  # Near top wall
            possible_directions.remove(UP) if UP in possible_directions else None
        if head_y >= GRID_HEIGHT - 2:  # Near bottom wall
            possible_directions.remove(DOWN) if DOWN in possible_directions else None
        if head_x <= 1:  # Near left wall
            possible_directions.remove(LEFT) if LEFT in possible_directions else None
        if head_x >= LOGICAL_GRID_WIDTH - 2:  # Near right wall - use logical width
            possible_directions.remove(RIGHT) if RIGHT in possible_directions else None
        
        # Remove directions that would hit snake body
        for dx, dy in possible_directions.copy():
            if (head_x + dx, head_y + dy) in self.snake:
                possible_directions.remove((dx, dy))
        
        # If there are still possible directions, choose one
        if possible_directions:
            self.direction = random.choice(possible_directions)
        else:
            # No good direction, just go opposite to avoid immediate collision
            dx, dy = self.direction
            self.direction = (-dx, -dy)
    
    def avoid_self(self):
        """AI logic to avoid hitting itself"""
        head_x, head_y = self.snake[0]
        possible_directions = [UP, DOWN, LEFT, RIGHT]
        
        # Remove the opposite of current direction to avoid sudden reversal
        dx, dy = self.direction
        opposite = (-dx, -dy)
        if opposite in possible_directions:
            possible_directions.remove(opposite)
        
        # Remove directions that would hit walls
        if head_y <= 1:  # Near top wall
            possible_directions.remove(UP) if UP in possible_directions else None
        if head_y >= GRID_HEIGHT - 2:  # Near bottom wall
            possible_directions.remove(DOWN) if DOWN in possible_directions else None
        if head_x <= 1:  # Near left wall
            possible_directions.remove(LEFT) if LEFT in possible_directions else None
        if head_x >= LOGICAL_GRID_WIDTH - 2:  # Near right wall - use logical width
            possible_directions.remove(RIGHT) if RIGHT in possible_directions else None
        
        # Remove directions that would hit snake body
        for dx, dy in possible_directions.copy():
            if (head_x + dx, head_y + dy) in self.snake:
                possible_directions.remove((dx, dy))
        
        # If there are still possible directions, choose one
        if possible_directions:
            self.direction = random.choice(possible_directions)
        # If no good directions, just keep going and let the collision happen
    
    def ai_decide_direction(self):
        """AI decides which direction to move based on food position"""
        head_x, head_y = self.snake[0]
        food_x, food_y = self.food_pos
        
        # Possible directions
        possible_directions = [UP, DOWN, LEFT, RIGHT]
        
        # Remove the opposite of current direction to avoid sudden reversal
        dx, dy = self.direction
        opposite = (-dx, -dy)
        if opposite in possible_directions:
            possible_directions.remove(opposite)
        
        # Remove directions that would hit walls
        if head_y <= 1:  # Near top wall
            possible_directions.remove(UP) if UP in possible_directions else None
        if head_y >= GRID_HEIGHT - 2:  # Near bottom wall
            possible_directions.remove(DOWN) if DOWN in possible_directions else None
        if head_x <= 1:  # Near left wall
            possible_directions.remove(LEFT) if LEFT in possible_directions else None
        if head_x >= LOGICAL_GRID_WIDTH - 2:  # Near right wall - use logical width
            possible_directions.remove(RIGHT) if RIGHT in possible_directions else None
        
        # Remove directions that would hit snake body
        for dx, dy in possible_directions.copy():
            if (head_x + dx, head_y + dy) in self.snake:
                possible_directions.remove((dx, dy)) if (dx, dy) in possible_directions else None
        
        # If there are still possible directions
        if possible_directions:
            # Calculate distance to food for each direction
            direction_scores = {}
            for dx, dy in possible_directions:
                new_x, new_y = head_x + dx, head_y + dy
                distance = abs(new_x - food_x) + abs(new_y - food_y)  # Manhattan distance
                direction_scores[(dx, dy)] = distance
            
            # Choose direction with smallest distance to food 80% of the time
            # 20% of the time, choose randomly to make the AI less predictable
            if random.random() < 0.8:
                # Sort by distance (ascending) and take the first (closest)
                best_direction = min(direction_scores.items(), key=lambda x: x[1])[0]
                self.direction = best_direction
            else:
                self.direction = random.choice(possible_directions)
        else:
            # No good directions, just keep current direction
            pass
    
    def reset_game(self):
        """Reset the game state after game over"""
        # Keep high score but reset current score
        self.score = 0
        self.game_over = False
        self.speed = GAME_SPEED
        self.frames = 0
        
        # Reset snake to center - use logical grid width
        self.snake = [(LOGICAL_GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = random.choice([UP, DOWN, LEFT, RIGHT])
        
        # Reset grid and create new food
        self.grid = [[EMPTY_CHAR for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.draw_border()
        self.create_food()
    
    def display_game(self):
        """Display the current game state on the screen"""
        splash = displayio.Group()
        self.display.show(splash)
        
        # Display game grid
        for y, row in enumerate(self.grid):
            line = ''.join(row)
            row_color = COLOR_SNAKE  # Default color
            
            # Create text area for this row
            text_area = label.Label(
                terminalio.FONT,
                text=line,
                x=LEFT_MARGIN + 20,  # Add extra margin to help center the narrower grid
                y=TOP_MARGIN + y * 14,  # Adjust line height as needed
                color=row_color
            )
            splash.append(text_area)
        
        # Display score and high score at the bottom
        score_text = f"Score: {self.score} - High: {self.high_score}"
        score_area = label.Label(
            terminalio.FONT,
            text=score_text,
            x=LEFT_MARGIN + 20,  # Match the extra margin
            y=TOP_MARGIN + GRID_HEIGHT * 14 + 10,  # Below the grid
            color=COLOR_BORDER
        )
        splash.append(score_area)
    
    def update(self):
        """Update the game state"""
        # AI decides direction
        self.ai_decide_direction()
        
        # Move the snake
        self.move_snake()
        
        # Update grid with current game state
        self.update_grid()
        
        # Display the updated game
        self.display_game()

def main():
    """Main function to run the Snake game"""
    display = initialise_display()
    game = SnakeGame(display)
    
    # Main game loop
    try:
        while True:
            game.update()
            time.sleep(game.speed)  # Use current game speed
    except KeyboardInterrupt:
        print("Game terminated by user")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import board
import displayio
import terminalio
import time
import random
import gc  # Import garbage collector
from adafruit_display_text import label
from adafruit_st7789 import ST7789

# Force garbage collection at the very start
gc.collect()

# Immediately free any unnecessary memory
displayio.release_displays()
gc.collect()

# Minimal constants for initial setup - more defined later when needed
# Display configuration
DISPLAY_WIDTH = 280
DISPLAY_HEIGHT = 240

# Physical display configuration
SPI = board.SPI()
TFT_CS = board.D5  # Chip select pin
TFT_DC = board.D16  # Data/command pin
TFT_RESET = board.D9  # Reset pin

# Minimal game settings - drastic reduction to avoid any 256-byte allocations
GRID_WIDTH = 16    # Drastically reduced width to avoid memory errors
GRID_HEIGHT = 8    # Drastically reduced height to avoid memory errors
GAME_SPEED = 0.15  # Delay between frames

# Directions (dx, dy)
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# Additional settings that will be defined later
HORIZONTAL_DOUBLE_WIDTH = True  # Flag for double-width rendering

def debug_print(*lines, delay=0.5):
    """Simplified debug print that uses minimal memory"""
    for line in lines:
        try:
            print(line)
            time.sleep(delay)
        except Exception:
            pass
    # Force garbage collection after printing
    gc.collect()

def initialise_display():
    """Minimal display initialization to reduce memory usage"""
    # Force garbage collection before display initialization
    gc.collect()
    
    try:
        # Create display bus with minimal operations
        display_bus = displayio.FourWire(
            SPI, 
            command=TFT_DC,
            chip_select=TFT_CS,
            reset=TFT_RESET
        )
        
        # Free memory before creating display
        gc.collect()
        
        # Create ST7789 display with minimal parameters
        display = ST7789(
            display_bus,
            width=DISPLAY_WIDTH,
            height=DISPLAY_HEIGHT,
            rowstart=20,
            rotation=270
        )
        
        # Print simple success message
        print("Display initialized")
        
        # Force garbage collection after display creation
        gc.collect()
        
        return display
        
    except Exception as e:
        print(f"Display error: {e}")
        time.sleep(1)
        # Try one more time with forced GC
        gc.collect()
        
        # Create minimal display objects
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
        
        gc.collect()
        return display

# Define game constants only after display initialization succeeds
def define_game_constants():
    """Define game constants only when needed to reduce startup memory usage"""
    global LEFT_MARGIN, RIGHT_MARGIN, TOP_MARGIN, BOTTOM_MARGIN
    global LOGICAL_GRID_WIDTH, SNAKE_SPEEDUP_FACTOR, MIN_GAME_SPEED
    global COLOR_SNAKE, COLOR_FOOD, COLOR_BORDER
    global SNAKE_HEAD_CHAR, SNAKE_BODY_CHAR, FOOD_CHAR, EMPTY_CHAR, BORDER_CHAR
    
    # Display margins
    LEFT_MARGIN = 10
    RIGHT_MARGIN = 10
    TOP_MARGIN = 20
    BOTTOM_MARGIN = 10
    
    # Game settings
    LOGICAL_GRID_WIDTH = GRID_WIDTH // 2 if HORIZONTAL_DOUBLE_WIDTH else GRID_WIDTH
    SNAKE_SPEEDUP_FACTOR = 0.98
    MIN_GAME_SPEED = 0.05
    
    # Colors
    COLOR_SNAKE = 0x00FF00  # Green
    COLOR_FOOD = 0xFF0000   # Red
    COLOR_BORDER = 0xFFFFFF # White
    
    # Game characters - using simpler characters to reduce memory usage
    SNAKE_HEAD_CHAR = 'O'   # Simplified head character
    SNAKE_BODY_CHAR = '#'   # Simplified body character
    FOOD_CHAR = '*'         # Simplified food character
    EMPTY_CHAR = ' '        # Empty space character
    BORDER_CHAR = '='       # Simplified border character
    
    # Force garbage collection after defining constants
    gc.collect()


class SnakeGame:
    """Snake game implementation - memory-optimized version"""
    
    def __init__(self, display):
        # Force garbage collection before initialization
        gc.collect()
        
        # Store display reference
        self.display = display
        
        # Initialize minimal game state
        self.game_over = False
        self.score = 0
        self.high_score = 0
        self.speed = GAME_SPEED
        self.frames = 0
        
        # Create grid with ultra-minimal memory allocations - cell by cell
        self.grid = []
        for _ in range(GRID_HEIGHT):
            # Create an empty row first
            row = []
            # Add individual cells to avoid any large allocations
            for _ in range(GRID_WIDTH):
                row.append(' ')  # Use a literal space to avoid even variable reference
                # Force periodic collection during cell creation
                if random.random() < 0.1:  # 10% chance per cell
                    gc.collect()
            # Append the row
            self.grid.append(row)
            # Force collection after each row
            gc.collect()
        
        # Initialize minimal snake in the middle
        self.snake = [(LOGICAL_GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        
        # Simplified direction choice to reduce memory usage
        dice = int(time.time() * 10) % 4
        self.direction = [UP, RIGHT, DOWN, LEFT][dice]
        
        # Food position
        self.food_pos = None
        
        # Force garbage collection before calling other methods
        gc.collect()
        
        # Initialize game elements
        self.create_food()
        self.draw_border()
        
        # Final garbage collection after initialization
        gc.collect()
        
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
        """Ultra-minimal grid update with micro-allocations to avoid 256-byte blocks"""
        # Force collection before update
        gc.collect()
        
        # Clear the grid in micro-chunks (except border)
        for y in range(1, GRID_HEIGHT-1):
            # Process 4 cells at a time
            for chunk_start in range(1, GRID_WIDTH-1, 4):
                chunk_end = min(chunk_start + 4, GRID_WIDTH-1)
                # Update cells in this micro-chunk
                for x in range(chunk_start, chunk_end):
                    self.grid[y][x] = ' '  # Use literal space to avoid even variable reference
                # Force collection after each chunk
                gc.collect()
        
        # Place food with careful bounds checking
        if self.food_pos:
            food_x, food_y = self.food_pos
            # Force collection before food placement
            gc.collect()
            
            # Extra cautious bounds checking
            if 0 <= food_y < GRID_HEIGHT:
                if HORIZONTAL_DOUBLE_WIDTH:
                    # Convert logical x to display x (multiply by 2)
                    display_x = food_x * 2
                    # Place food in a single cell with strict bounds checking
                    if 0 <= display_x < GRID_WIDTH:
                        try:
                            self.grid[food_y][display_x] = FOOD_CHAR
                        except IndexError:
                            # Fail silently if we hit an index error
                            pass
                else:
                    # Normal placement with strict bounds checking
                    if 0 <= food_x < GRID_WIDTH:
                        try:
                            self.grid[food_y][food_x] = FOOD_CHAR
                        except IndexError:
                            # Fail silently if we hit an index error
                            pass
        
        # Force collection before snake placement
        gc.collect()
        
        # Place snake in chunks to avoid large memory operations
        for i in range(len(self.snake)):
            # Force collection periodically during snake placement
            if i % 2 == 0:
                gc.collect()
                
            # Get snake segment with bounds checking
            try:
                x, y = self.snake[i]
            except IndexError:
                continue
                
            # Skip if out of bounds
            if not (0 <= y < GRID_HEIGHT):
                continue
                
            # Place segment with double-width handling
            if HORIZONTAL_DOUBLE_WIDTH:
                # Convert logical x to display x
                display_x = x * 2
                
                # Bounds check
                if 0 <= display_x < GRID_WIDTH:
                    try:
                        # Place first part of segment
                        self.grid[y][display_x] = SNAKE_HEAD_CHAR if i == 0 else SNAKE_BODY_CHAR
                        
                        # Place second part if in bounds
                        if display_x + 1 < GRID_WIDTH:
                            self.grid[y][display_x+1] = SNAKE_HEAD_CHAR if i == 0 else SNAKE_BODY_CHAR
                    except IndexError:
                        # Fail silently on index errors
                        pass
            else:
                # Normal placement with bounds checking
                if 0 <= x < GRID_WIDTH:
                    try:
                        self.grid[y][x] = SNAKE_HEAD_CHAR if i == 0 else SNAKE_BODY_CHAR
                    except IndexError:
                        # Fail silently on index errors
                        pass
                        
        # Final collection after grid update
        gc.collect()
    
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
        """Ultra-minimal display with micro-chunking to avoid 256-byte allocations"""
        # Force garbage collection before display
        gc.collect()
        
        try:
            # Create a minimal display group
            splash = displayio.Group()
            self.display.show(splash)
            
            # Display grid one micro-chunk at a time
            for y in range(GRID_HEIGHT):
                # Force collection before each row
                gc.collect()
                
                # Process the row in 4-character chunks
                for chunk_start in range(0, GRID_WIDTH, 4):
                    # Force collection before each chunk
                    gc.collect()
                    
                    # Calculate the end of this chunk
                    chunk_end = min(chunk_start + 4, GRID_WIDTH)
                    
                    # Create a minimal text string for just this chunk
                    chunk_text = ""
                    for x in range(chunk_start, chunk_end):
                        chunk_text += self.grid[y][x]
                    
                    # Calculate position for this chunk
                    chunk_x = LEFT_MARGIN + (chunk_start * 6)  # 6 pixels per character
                    
                    try:
                        # Create a minimal label for just this small chunk
                        chunk_label = label.Label(
                            terminalio.FONT,
                            text=chunk_text,
                            x=chunk_x,
                            y=TOP_MARGIN + y * 14,
                            color=0x00FF00  # Green
                        )
                        splash.append(chunk_label)
                        
                        # Force collection after creating each label
                        gc.collect()
                    except MemoryError:
                        # If memory error, skip this chunk and continue
                        pass
            
            # Display minimal score instead of formatted text
            try:
                # Just show simple score without formatting to minimize memory use
                simple_score = f"S:{self.score}"
                
                score_label = label.Label(
                    terminalio.FONT,
                    text=simple_score,
                    x=LEFT_MARGIN,
                    y=TOP_MARGIN + GRID_HEIGHT * 14 + 10,
                    color=0xFFFFFF  # White
                )
                splash.append(score_label)
            except MemoryError:
                # If we can't show score, just continue
                pass
                
        except Exception as e:
            # Handle any errors silently to keep game running
            print(f"Display error: {e}")
            
        # Final garbage collection
        gc.collect()
    
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
    """Ultra minimal main function to avoid all 256 byte allocations"""
    # Repeatedly force garbage collection at startup
    for _ in range(5):
        gc.collect()
        time.sleep(0.1)
        
    try:
        print("Starting with extreme memory conservation...")
        
        # Step 1: Initialize display with absolute minimal overhead
        print("Display init...")
        display = None
        gc.collect()
        display = initialise_display()
        
        # Force aggressive collection after display init
        for _ in range(3):
            gc.collect()
            time.sleep(0.1)
        
        # Step 2: Define constants only after sufficient collection
        print("Constants...")
        define_game_constants()
        
        # More aggressive collection
        for _ in range(3):
            gc.collect()
            time.sleep(0.1)
        
        # Step 3: Create game with minimum memory footprint
        print("Creating game...")
        game = None  # Ensure no reference exists
        gc.collect()
        game = SnakeGame(display)
        
        # Final pre-game collection
        for _ in range(3):
            gc.collect()
            time.sleep(0.1)
        
        print("Game ready!")
        
        # Step 4: Super conservative game loop with extreme error handling
        update_count = 0
        
        while True:
            try:
                # Update count for gradual startup
                update_count += 1
                
                # Force collection every frame
                gc.collect()
                
                # Initially only update every other frame to reduce memory pressure
                if update_count < 20 and update_count % 2 == 0:
                    time.sleep(game.speed)
                    continue
                
                # Update game with minimal memory usage
                game.update()
                
                # Brief delay based on game speed
                time.sleep(game.speed)
                
            except MemoryError as e:
                # Detailed error reporting and very aggressive collection
                print(f"Memory error: {e}")
                for _ in range(5):
                    gc.collect()
                    time.sleep(0.2)
                
            except Exception as e:
                # Other error handling
                print(f"Error: {e}")
                gc.collect()
                time.sleep(0.5)
                
    except Exception as e:
        # Fatal error handling with detailed reporting
        print(f"Fatal error: {e}")
        for _ in range(5):
            gc.collect()
            time.sleep(0.5)


if __name__ == "__main__":
    # Extremely minimal startup with forced memory cleanup
    gc.collect()
    main()

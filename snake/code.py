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

# Check if we're running on CircuitPython (has mem_free) or standard Python
try:
    print(f"Initial free memory: {gc.mem_free()} bytes")
    has_mem_free = True
except AttributeError:
    print("Running in simulator mode - memory stats not available")
    has_mem_free = False

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

# Game board dimensions - optimized for memory constraints while maintaining playability
GRID_WIDTH = 10    # Slightly increased from absolute minimum
GRID_HEIGHT = 8    # Slightly increased from absolute minimum
GAME_SPEED = 0.15  # Delay between frames

# Directions (dx, dy)
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# Additional settings that will be defined later
HORIZONTAL_DOUBLE_WIDTH = True  # Flag for double-width rendering

def debug_print(*lines, delay=0.2):
    """Memory-efficient debug print function"""
    gc.collect()  # Collect before printing
    for line in lines:
        try:
            print(line)
            # Only sleep if delay is significant
            if delay > 0.05:
                time.sleep(delay)
        except Exception as e:
            print(f"Print error: {e}")
    
    # Force garbage collection after printing
    gc.collect()

def initialise_display():
    """Memory-optimized display initialization"""
    # Force garbage collection before display initialization
    gc.collect()
    if has_mem_free:
        print(f"Before display init: {gc.mem_free()} bytes")
    
    try:
        # Create display bus
        display_bus = displayio.FourWire(
            SPI, 
            command=TFT_DC,
            chip_select=TFT_CS,
            reset=TFT_RESET
        )
        
        # Free memory before creating display
        gc.collect()
        if has_mem_free:
            print(f"After bus creation: {gc.mem_free()} bytes")
        
        # Create ST7789 display
        display = ST7789(
            display_bus,
            width=DISPLAY_WIDTH,
            height=DISPLAY_HEIGHT,
            rowstart=20,
            rotation=270
        )
        
        # Force garbage collection after display creation
        gc.collect()
        if has_mem_free:
            print(f"After display init: {gc.mem_free()} bytes")
        
        return display
        
    except Exception as e:
        print(f"Display error: {e}")
        gc.collect()
        
        # If we got an error, try to clean up any partial objects
        try:
            del display_bus
        except:
            pass
            
        gc.collect()
        print("Retrying display init after error...")
        
        # Try one more time with more careful approach
        display_bus = displayio.FourWire(
            SPI, 
            command=TFT_DC,
            chip_select=TFT_CS,
            reset=TFT_RESET
        )
        gc.collect()  # Collect after bus creation
        
        display = ST7789(
            display_bus,
            width=DISPLAY_WIDTH,
            height=DISPLAY_HEIGHT,
            rowstart=20,
            rotation=270
        )
        gc.collect()  # Collect after display creation
        
        return display

# Define game constants only after display initialization succeeds
def define_game_constants():
    """Define game constants only when needed to reduce startup memory usage"""
    global LEFT_MARGIN, RIGHT_MARGIN, TOP_MARGIN, BOTTOM_MARGIN
    global LOGICAL_GRID_WIDTH, SNAKE_SPEEDUP_FACTOR, MIN_GAME_SPEED
    global COLOR_SNAKE, COLOR_FOOD, COLOR_BORDER
    global SNAKE_HEAD_CHAR, SNAKE_BODY_CHAR, FOOD_CHAR, EMPTY_CHAR, BORDER_CHAR
    global LINE_HEIGHT, CHAR_WIDTH
    
    # If memory tracking is available, report memory before defining constants
    if has_mem_free:
        print(f"Before defining constants: {gc.mem_free()} bytes")
        
    # Display margins and layout
    LEFT_MARGIN = 10
    RIGHT_MARGIN = 10
    TOP_MARGIN = 20
    BOTTOM_MARGIN = 10
    LINE_HEIGHT = 14  # Vertical spacing for text rows
    CHAR_WIDTH = 6    # Horizontal spacing for characters
    
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
    
    # Report memory after defining constants
    if has_mem_free:
        print(f"After defining constants: {gc.mem_free()} bytes")


class SnakeGame:
    """Snake game implementation with memory-efficient techniques"""
    
    def __init__(self, display):
        # Force memory cleanup and monitor usage
        gc.collect()
        
        # Track memory if available
        if has_mem_free:
            initial_mem = gc.mem_free()
            print(f"Starting game init, memory: {initial_mem} bytes")
        
        # Store display reference and create splash group once 
        # (per CircuitPython memory saving tips)
        self.display = display
        self.splash = displayio.Group()
        
        # Initialize minimal game state
        self.game_over = False
        self.score = 0
        self.high_score = 0
        self.speed = GAME_SPEED
        self.frames = 0
        
        # Create the grid all at once - surprisingly, this is more memory efficient
        # in CircuitPython than creating it row by row or cell by cell
        gc.collect()
        if has_mem_free:
            before_grid = gc.mem_free()
            print(f"Before grid creation: {before_grid} bytes")
        
        # Pre-allocate the full board at once
        self.grid = [[EMPTY_CHAR for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        
        gc.collect()
        if has_mem_free:
            after_grid = gc.mem_free()
            print(f"After grid creation: {after_grid} bytes (used {before_grid - after_grid} bytes)")
        
        # Initialize minimal snake in the middle
        self.snake = [(LOGICAL_GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        
        # Simplified direction choice to reduce memory usage
        # Using time instead of random to reduce memory pressure during initialization
        dice = int(time.time() * 10) % 4
        self.direction = [UP, RIGHT, DOWN, LEFT][dice]
        
        # Food position
        self.food_pos = None
        
        # Force garbage collection before calling other methods
        gc.collect()
        
        # Initialize game elements
        self.create_food()
        self.draw_border()
        
        # Final garbage collection and memory usage report
        gc.collect()
        if has_mem_free:
            final_mem = gc.mem_free()
            print(f"Game ready, memory: {final_mem} bytes (used {initial_mem - final_mem} bytes)")
        
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
        """Create food at a random empty location - memory-optimized version"""
        # Force collection before starting
        gc.collect()
        if has_mem_free:
            initial_mem = gc.mem_free()
            print(f"Creating food, memory: {initial_mem} bytes")
        
        # Use a more memory-efficient algorithm for food placement
        # Instead of checking if (x,y) not in snake (which creates temporary tuples),
        # we'll do direct coordinate comparison
        
        # First approach: Try a simple random position a few times
        # This avoids the need for double scanning the grid
        max_attempts = 10
        for _ in range(max_attempts):
            # Generate random position (avoid borders)
            x = random.randint(1, LOGICAL_GRID_WIDTH-2)
            y = random.randint(1, GRID_HEIGHT-2)
            
            # Check if position is not occupied by snake
            position_is_free = True
            for snake_x, snake_y in self.snake:
                if x == snake_x and y == snake_y:
                    position_is_free = False
                    break
            
            # If we found a free position, use it
            if position_is_free:
                self.food_pos = (x, y)
                gc.collect()
                if has_mem_free:
                    final_mem = gc.mem_free()
                    print(f"Food created at ({x},{y}), memory: {final_mem} bytes")
                return
                
        # If we couldn't find a position with the fast approach, use a more thorough method
        # Collect empty cells' coordinates in small batches to avoid large allocations
        gc.collect()
        empty_cells = []  # Will hold up to 4 empty cells at a time
        
        # Scan grid by small ranges to find empty cells
        for y in range(1, GRID_HEIGHT-1):
            for x in range(1, LOGICAL_GRID_WIDTH-1):
                # Check if position is free
                position_is_free = True
                for snake_x, snake_y in self.snake:
                    if x == snake_x and y == snake_y:
                        position_is_free = False
                        break
                
                # If position is free, add it to our small collection
                if position_is_free:
                    empty_cells.append((x, y))
                    # If we have 4 cells, that's enough to choose from
                    if len(empty_cells) >= 4:
                        break
            
            # If we have enough empty cells, no need to continue scanning
            if len(empty_cells) >= 4:
                break
        
        # If we found any empty cells, choose one randomly
        if empty_cells:
            self.food_pos = random.choice(empty_cells)
        else:
            # Last resort fallback to fixed position
            self.food_pos = (1, 1)
        
        # Final garbage collection
        gc.collect()
        if has_mem_free:
            final_mem = gc.mem_free()
            print(f"Food created (thorough method), memory: {final_mem} bytes")
    
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
        """Display the game using techniques that work with both real hardware and simulator"""
        # Monitor memory usage
        gc.collect()
        if has_mem_free:
            initial_mem = gc.mem_free()
            print(f"Display start, memory: {initial_mem} bytes")
        
        try:
            # Clear the existing display group (don't recreate it)
            while len(self.splash) > 0:
                self.splash.pop()
            
            # Show our reused splash group
            self.display.show(self.splash)
            
            # Create individual row labels - works better with simulator and real hardware
            for y, row in enumerate(self.grid):
                # Join this row into a string
                row_text = "".join(row)
                
                # Create a label for this row
                row_label = label.Label(
                    terminalio.FONT,
                    text=row_text,
                    x=LEFT_MARGIN,
                    y=TOP_MARGIN + (y * LINE_HEIGHT),
                    color=COLOR_SNAKE
                )
                
                # Add the row label to our display group
                self.splash.append(row_label)
                
                # Collect garbage periodically during display updates on real hardware
                if has_mem_free and y % 2 == 0:
                    gc.collect()
            
            # Display minimal score with more consistent positioning
            try:
                # Show score with minimal formatting
                score_text = f"Score: {self.score}  High: {self.high_score}"
                
                score_label = label.Label(
                    terminalio.FONT,
                    text=score_text,
                    x=LEFT_MARGIN,
                    y=TOP_MARGIN + (GRID_HEIGHT * LINE_HEIGHT) + 10,
                    color=COLOR_BORDER
                )
                self.splash.append(score_label)
            except MemoryError:
                # Fall back to ultra minimal score display if needed
                try:
                    minimal_score = f"S:{self.score}"
                    score_label = label.Label(
                        terminalio.FONT,
                        text=minimal_score,
                        x=LEFT_MARGIN,
                        y=TOP_MARGIN + (GRID_HEIGHT * LINE_HEIGHT) + 10,
                        color=COLOR_BORDER
                    )
                    self.splash.append(score_label)
                except:
                    pass  # If all else fails, continue without score display
            
            # Monitor memory after rendering if available
            gc.collect()
            if has_mem_free:
                after_render = gc.mem_free()
                if initial_mem - after_render > 500:  # Only log if significant change
                    print(f"Display used {initial_mem - after_render} bytes")
                    
        except Exception as e:
            # Log display errors
            print(f"Display error: {e}")
            gc.collect()
        
        # Force garbage collection after display update
        gc.collect()
    
    def update(self):
        """Update game state with memory-efficient techniques"""
        # Monitor memory usage for diagnostics
        gc.collect()
        if has_mem_free:
            initial_mem = gc.mem_free()
            print(f"Update start, memory: {initial_mem} bytes")
        
        try:
            if not self.game_over:
                # 1. AI decides direction
                self.ai_decide_direction()
                
                # 2. Move the snake
                self.move_snake()
                
                # 3. Update grid with current game state
                self.update_grid()
            
            # 4. Display the updated game
            self.display_game()
            
            # Monitor memory usage if available
            gc.collect()
            if has_mem_free:
                after_update = gc.mem_free()
                if initial_mem - after_update > 500:  # Only log if significant change
                    print(f"Update used {initial_mem - after_update} bytes")
        
        except MemoryError as e:
            # Handle memory errors
            print(f"Memory error in update: {e}")
            if has_mem_free:
                print(f"Free memory: {gc.mem_free()} bytes")
            gc.collect()
            if has_mem_free:
                print(f"After collection: {gc.mem_free()} bytes")
            
        except Exception as e:
            # General error handling
            print(f"Update error: {e}")
            gc.collect()

def main():
    """Main function with memory-efficient techniques for both CircuitPython and standard Python"""
    # Initial memory diagnostics
    gc.collect()
    if has_mem_free:
        print(f"Starting Snake, available memory: {gc.mem_free()} bytes")
    else:
        print("Starting Snake (memory stats not available)")
    
    try:
        # Release any existing displays to free memory
        displayio.release_displays()
        gc.collect()
        
        # Step 1: Initialize display
        print("Initializing display...")
        display = initialise_display()
        
        # Step 2: Define game constants
        print("Defining game constants...")
        gc.collect()
        define_game_constants()
        
        # Step 3: Create game instance with optimized memory usage
        print("Creating game...")
        gc.collect()
        game = SnakeGame(display)
        
        # Step 4: Main game loop with progressive startup to minimize memory pressure
        print("Starting game loop")
        update_count = 0
        
        while True:
            try:
                # Update count for gradual startup
                update_count += 1
                
                # Force collection before update
                gc.collect()
                
                # For the first few frames, update every other frame to reduce memory pressure
                if update_count < 20 and update_count % 2 == 0:
                    time.sleep(game.speed)
                    continue
                
                # Update the game state
                game.update()
                
                # Brief delay to control game speed
                time.sleep(game.speed)
                
                # Handle game over state - no need for separate call as it's handled in the update method
                
            except MemoryError as e:
                # Memory error diagnostics and recovery
                print(f"Memory error: {e}")
                if has_mem_free:
                    print(f"Free memory: {gc.mem_free()} bytes")
                gc.collect()
                if has_mem_free:
                    print(f"After collection: {gc.mem_free()} bytes")
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                print("Game terminated by user")
                raise
                
    except KeyboardInterrupt:
        print("Game terminated by user")
        
    except Exception as e:
        # General error handling
        print(f"Fatal error: {e}")
        gc.collect()


if __name__ == "__main__":
    # Initial garbage collection
    gc.collect()
    
    try:
        # Start the game
        main()
    except Exception as e:
        # Last resort error handling that works in both environments
        print(f"Critical error: {e}")
        gc.collect()

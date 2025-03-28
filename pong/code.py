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

# Minimal initial game settings
BOARD_WIDTH = 30    # Reduced from 40 to save memory
BOARD_HEIGHT = 12   # Reduced from 16 to save memory
GAME_DELAY = 0.07   # Delay between frames


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


# Simplified number patterns - only defined when needed in score drawing
def get_digit_pattern(digit):
    """Get a simplified digit pattern using less memory"""
    patterns = {
        0: ["===", "= =", "= =", "= =", "==="],
        1: [" = ", "== ", " = ", " = ", "==="],
        2: ["===", "  =", "===", "=  ", "==="],
        3: ["===", "  =", "===", "  =", "==="],
        4: ["= =", "= =", "===", "  =", "  ="],
        5: ["===", "=  ", "===", "  =", "==="],
        6: ["===", "=  ", "===", "= =", "==="],
        7: ["===", "  =", "  =", "  =", "  ="],
        8: ["===", "= =", "===", "= =", "==="],
        9: ["===", "= =", "===", "  =", "==="]
    }
    return patterns.get(digit, patterns[0])


class PongGame:
    """Ultra-minimal Pong game implementation to reduce memory usage at startup"""
    
    def __init__(self, display):
        # Force memory cleanup before initialization
        gc.collect()
        
        # Store display reference
        self.display = display
        
        # Initialize scores
        self.player_score = 0
        self.cpu_score = 0
        self.game_over = False
        self.winner = None
        
        # Initialize board as empty list (not 2D array) to reduce memory usage
        self.board = None  # Will be created on first update
        
        # Set up minimal paddle positions
        self.player_y = BOARD_HEIGHT // 2 - 1
        self.cpu_y = BOARD_HEIGHT // 2 - 1
        
        # Set up minimal ball state
        self.ball_x = BOARD_WIDTH // 2
        self.ball_y = BOARD_HEIGHT // 2
        self.ball_dx = 1 if random.random() > 0.5 else -1  # Simplified random choice
        self.ball_dy = 0  # Start with horizontal movement to reduce complexity
        self.ball_delay = MIN_BALL_DELAY
        self.frame_count = 0
        
        # Force garbage collection before first update
        gc.collect()
        
        # Create board on first update
        self.create_minimal_board()
        
        # Final garbage collection
        gc.collect()
    
    def create_minimal_board(self):
        """Create a new game board with absolute minimal memory usage"""
        # Force garbage collection before creating board
        gc.collect()
        
        # Create empty board - one row at a time to reduce memory pressure
        board = []
        for _ in range(BOARD_HEIGHT):
            # Use single operation to create each row
            board.append([EMPTY_CHAR] * BOARD_WIDTH)
            # Force collection after each row to minimize peak usage
            gc.collect()
        
        # Store the board
        self.board = board
        
        # Final garbage collection
        gc.collect()
    
    def update_board(self):
        """Ultra minimal board update for very low memory usage"""
        # Force garbage collection before board update
        gc.collect()
        
        # Make sure board exists
        if self.board is None:
            self.create_minimal_board()
        
        # Clear the board (in-place to avoid reallocating)
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                self.board[y][x] = EMPTY_CHAR
            # Collect after each row
            if y % 4 == 0:
                gc.collect()
                
        # Add minimal center net
        center_x = BOARD_WIDTH // 2
        for y in range(0, BOARD_HEIGHT, 2):
            if y < BOARD_HEIGHT:
                self.board[y][center_x] = NET_CHAR
        
        # Add simplified score display - just single digits
        if self.player_score < 10:
            self.board[1][2] = str(self.player_score)
        else:
            self.board[1][2] = "9+"
            
        if self.cpu_score < 10:
            self.board[1][BOARD_WIDTH-3] = str(self.cpu_score)
        else:
            self.board[1][BOARD_WIDTH-3] = "9+"
        
        # Add paddles
        for i in range(PADDLE_SIZE):
            py = self.player_y + i
            cy = self.cpu_y + i
            if 0 <= py < BOARD_HEIGHT:
                self.board[py][1] = PADDLE_CHAR  # Player paddle
            if 0 <= cy < BOARD_HEIGHT:
                self.board[cy][BOARD_WIDTH - 2] = PADDLE_CHAR  # CPU paddle
        
        # Add ball
        if 0 <= self.ball_y < BOARD_HEIGHT and 0 <= self.ball_x < BOARD_WIDTH:
            self.board[self.ball_y][self.ball_x] = BALL_CHAR
            
        # Force garbage collection after update
        gc.collect()
    
    def move_ball(self):
        """Move the ball and handle collisions - memory optimized version"""
        # Increment frame counter
        self.frame_count += 1
        
        # Only move the ball every ball_delay frames to control speed
        if self.frame_count < self.ball_delay:
            return
        
        # Reset frame counter
        self.frame_count = 0
        
        # Calculate new position with simplified logic to save memory
        # Determine if we move diagonally this frame
        if self.ball_dy != 0:  # Ball is moving diagonally
            # Simplify random check to reduce memory usage
            diagonal_move = True
            if self.frame_count % 3 == 0:  # Deterministic approach instead of random
                new_x = self.ball_x  # Don't move horizontally this frame
            else:
                new_x = self.ball_x + self.ball_dx
            new_y = self.ball_y + self.ball_dy
        else:  # Ball is moving horizontally
            new_x = self.ball_x + self.ball_dx
            new_y = self.ball_y
        
        # Handle top/bottom wall collisions - bounds checking
        if new_y < 0:
            self.ball_dy = 1  # Bounce down
            new_y = 0
        elif new_y >= BOARD_HEIGHT:
            self.ball_dy = -1  # Bounce up
            new_y = BOARD_HEIGHT - 1
        
        # Handle paddle collisions with simplified checks
        player_hit = False
        cpu_hit = False
        
        # Player paddle collision check
        if (new_x == 1 or new_x == 2) and self.player_y <= new_y < self.player_y + PADDLE_SIZE:
            player_hit = True
            self.ball_dx = 1  # Move right after hitting player paddle
            
            # Simplified paddle physics - 3 zones
            relative_hit = new_y - self.player_y  # Where ball hit paddle (0 to PADDLE_SIZE-1)
            
            # Top third = up, middle third = straight, bottom third = down
            if relative_hit < PADDLE_SIZE // 3:
                self.ball_dy = -1  # Up
            elif relative_hit < 2 * (PADDLE_SIZE // 3):
                self.ball_dy = 0   # Straight
            else:
                self.ball_dy = 1   # Down
            
            # Speed up the ball 
            self.ball_delay = max(1, int(self.ball_delay * BALL_ACCELERATION))
        
        # CPU paddle collision check
        elif (new_x == BOARD_WIDTH - 2 or new_x == BOARD_WIDTH - 3) and self.cpu_y <= new_y < self.cpu_y + PADDLE_SIZE:
            cpu_hit = True
            self.ball_dx = -1  # Move left after hitting CPU paddle
            
            # Simplified paddle physics - same 3 zones
            relative_hit = new_y - self.cpu_y
            
            # Top third = up, middle third = straight, bottom third = down
            if relative_hit < PADDLE_SIZE // 3:
                self.ball_dy = -1  # Up
            elif relative_hit < 2 * (PADDLE_SIZE // 3):
                self.ball_dy = 0   # Straight
            else:
                self.ball_dy = 1   # Down
            
            # Speed up the ball
            self.ball_delay = max(1, int(self.ball_delay * BALL_ACCELERATION))
        
        # Handle scoring
        if new_x < 0:
            # CPU scores
            self.cpu_score += 1
            self.reset_ball()
            # Force garbage collection after scoring
            gc.collect()
            return
        elif new_x >= BOARD_WIDTH:
            # Player scores
            self.player_score += 1
            self.reset_ball()
            # Force garbage collection after scoring
            gc.collect()
            return
        
        # Update ball position
        self.ball_x = new_x
        self.ball_y = new_y
        
        # Check for game over
        if self.player_score >= WINNING_SCORE:
            self.game_over = True
            self.winner = "PLAYER"
            # Force garbage collection after game over
            gc.collect()
        elif self.cpu_score >= WINNING_SCORE:
            self.game_over = True
            self.winner = "CPU"
            # Force garbage collection after game over
            gc.collect()
    
    def reset_ball(self):
        """Reset the ball to the center with a random direction"""
        self.ball_x = BOARD_WIDTH // 2
        self.ball_y = BOARD_HEIGHT // 2
        self.ball_dx = random.choice([-1, 1])
        self.ball_dy = random.choice([-1, 0, 1])
        # Reset ball speed to initial speed (like original Pong)
        self.ball_delay = MIN_BALL_DELAY
        self.frame_count = 0
    
    def move_player_paddle(self, direction):
        """Move the player's paddle"""
        # Original Pong paddles couldn't reach the top of the screen
        if direction == -1 and self.player_y > 1:  # Can't reach very top
            self.player_y -= PADDLE_SPEED
        elif direction == 1 and self.player_y + PADDLE_SIZE < BOARD_HEIGHT:
            self.player_y += PADDLE_SPEED
    
    def move_cpu_paddle(self):
        """Move the CPU's paddle - memory optimized version"""
        # Only move if the ball is coming toward the CPU
        # This saves unnecessary computation and memory usage
        if self.ball_dx <= 0:
            return  # Ball moving away from CPU, don't bother moving
        
        # Deterministic approach to reduce memory usage from random()
        # Use frame counter and CPU_DIFFICULTY to decide if optimal move
        make_optimal_move = ((self.frame_count + 5) % 10 < int(CPU_DIFFICULTY * 10))
        
        if make_optimal_move:
            # Move optimally - simplified calculation
            paddle_middle = self.cpu_y + PADDLE_SIZE // 2
            
            # Simplified decision logic
            if self.ball_y > paddle_middle and self.cpu_y + PADDLE_SIZE < BOARD_HEIGHT:
                # Ball is below paddle middle, move down
                self.cpu_y += PADDLE_SPEED
            elif self.ball_y < paddle_middle and self.cpu_y > 1:
                # Ball is above paddle middle, move up
                self.cpu_y -= PADDLE_SPEED
        else:
            # Make a sub-optimal move - simplified random choice
            # Use a different mod of frame_count for CPU vs player to avoid synchronization
            move = ((self.frame_count + 1) % 3) - 1  # Gives -1, 0, or 1
            
            # Apply the move with bounds checking
            if move == -1 and self.cpu_y > 1:
                self.cpu_y -= PADDLE_SPEED
            elif move == 1 and self.cpu_y + PADDLE_SIZE < BOARD_HEIGHT:
                self.cpu_y += PADDLE_SPEED
    
    def simulate_player_move(self):
        """Simulate player paddle movement - memory-optimized version"""
        # Only process movement if the ball is moving toward the player
        # This saves unnecessary computation and memory usage
        if self.ball_dx >= 0:
            return  # Ball moving away from player, don't bother moving
            
        # Simplify AI decision to reduce memory usage
        # Use frame counter to make this deterministic instead of random
        make_optimal_move = (self.frame_count % 10 < int(PLAYER_DIFFICULTY * 10))
        
        if make_optimal_move:
            # Move optimally
            paddle_middle = self.player_y + PADDLE_SIZE // 2
            
            # Simplified decision logic
            if self.ball_y > paddle_middle and self.player_y + PADDLE_SIZE < BOARD_HEIGHT:
                # Ball is below paddle middle, move down
                self.player_y += PADDLE_SPEED
            elif self.ball_y < paddle_middle and self.player_y > 1:
                # Ball is above paddle middle, move up
                self.player_y -= PADDLE_SPEED
        else:
            # Make a mistake occasionally
            # Simplified random choice using frame counter
            move = (self.frame_count % 3) - 1  # Gives -1, 0, or 1
            
            # Apply the move with bounds checking
            if move == -1 and self.player_y > 1:
                self.player_y -= PADDLE_SPEED
            elif move == 1 and self.player_y + PADDLE_SIZE < BOARD_HEIGHT:
                self.player_y += PADDLE_SPEED
    
    def display_game(self):
        """Ultra minimal display method for extremely low memory usage"""
        # Force garbage collection before display
        gc.collect()
        
        try:
            # Create a minimal display group
            splash = displayio.Group()
            self.display.show(splash)
            
            # Only display 2 rows at a time to minimize memory usage
            for y_chunk in range(0, BOARD_HEIGHT, 2):
                # Collect garbage between chunks
                gc.collect()
                
                # Process two rows at a time
                for y_offset in range(2):
                    y = y_chunk + y_offset
                    if y < BOARD_HEIGHT:
                        # Join the row into a string
                        row_text = ''.join(self.board[y])
                        
                        # Create a label for this row
                        try:
                            row_label = label.Label(
                                terminalio.FONT,
                                text=row_text,
                                x=LEFT_MARGIN,
                                y=TOP_MARGIN + y * LINE_HEIGHT,
                                color=0x00FF00
                            )
                            splash.append(row_label)
                        except MemoryError:
                            # If we can't create the label, just continue
                            pass
                
                # Force garbage collection after each chunk
                gc.collect()
        
        except Exception as e:
            # Simple error handling
            print(f"Display error: {e}")
            gc.collect()
        
        # Final garbage collection
        gc.collect()
    
    def update(self):
        """Bare minimum update method for ultra-low memory usage"""
        # Force garbage collection at start
        gc.collect()
        
        # Use a minimal try/except to handle any memory errors
        try:
            # Process in strict order of importance
            
            # 1. Move ball
            if not self.game_over and self.frame_count % 3 == 0:
                self.move_ball()
                gc.collect()
            
            # 2. Move paddles (only every other frame to save memory)
            if not self.game_over and self.frame_count % 2 == 0:
                # CPU paddle
                self.move_cpu_paddle()
                # Player paddle
                self.simulate_player_move()
                gc.collect()
            
            # 3. Update board
            self.update_board()
            gc.collect()
            
            # 4. Display game
            self.display_game()
            
            # Increment frame counter
            self.frame_count += 1
            if self.frame_count > 10000:
                self.frame_count = 0
        
        except MemoryError:
            # If we hit a memory error, just collect and continue
            print("Memory error in update")
            gc.collect()
        
        # Final garbage collection
        gc.collect()
    
    def restart_game(self):
        """Ultra minimal game restart for very low memory usage"""
        # Force garbage collection before restart
        gc.collect()
        
        # Free display resources
        splash = displayio.Group()
        self.display.show(splash)
        gc.collect()
        
        # Reset game state with minimal operations
        self.player_score = 0
        self.cpu_score = 0
        self.game_over = False
        self.winner = None
        
        # Reset paddle positions
        self.player_y = BOARD_HEIGHT // 2 - 1
        self.cpu_y = BOARD_HEIGHT // 2 - 1
        
        # Reset ball
        self.ball_x = BOARD_WIDTH // 2
        self.ball_y = BOARD_HEIGHT // 2
        self.ball_dx = 1 if random.random() > 0.5 else -1
        self.ball_dy = 0
        self.ball_delay = MIN_BALL_DELAY
        self.frame_count = 0
        
        # Force garbage collection after state reset
        gc.collect()
        
        # Brief pause before resuming
        time.sleep(1)


# Define remaining game constants only after display initialization succeeds
# This delays memory allocation until absolutely needed
def define_game_constants():
    """Define game constants - only called after display init succeeds"""
    global LEFT_MARGIN, RIGHT_MARGIN, TOP_MARGIN, BOTTOM_MARGIN, CHAR_WIDTH, LINE_HEIGHT
    global PADDLE_CHAR, BALL_CHAR, EMPTY_CHAR, BORDER_CHAR, NET_CHAR
    global PADDLE_SIZE, PADDLE_SPEED, MIN_BALL_DELAY, MAX_BALL_DELAY
    global BALL_ACCELERATION, CPU_DIFFICULTY, PLAYER_DIFFICULTY, WINNING_SCORE
    global NUMBER_PATTERNS
    
    # Display margins and character sizes
    LEFT_MARGIN = 10
    RIGHT_MARGIN = 10
    TOP_MARGIN = 20
    BOTTOM_MARGIN = 20
    CHAR_WIDTH = 6
    LINE_HEIGHT = 15
    
    # Game characters - using simpler characters to reduce memory usage
    PADDLE_CHAR = '█'  # Paddle character
    BALL_CHAR = 'O'    # Ball character (simple 'O' uses less memory than '●')
    EMPTY_CHAR = ' '   # Empty space character
    BORDER_CHAR = '='  # Border character (simple '=' uses less memory than '═')
    NET_CHAR = '|'     # Net character (simple '|' uses less memory than '┊')
    
    # Game settings - simpler values
    PADDLE_SIZE = 3    # Paddle height
    PADDLE_SPEED = 1   # How fast paddles move
    MIN_BALL_DELAY = 2 # Initial ball speed
    MAX_BALL_DELAY = 2 # Maximum ball speed
    BALL_ACCELERATION = 0.85
    CPU_DIFFICULTY = 0.75
    PLAYER_DIFFICULTY = 0.65
    WINNING_SCORE = 11
    
    # Number patterns for scores - simplified for memory efficiency
    # We'll define these when needed in the game class instead


def main():
    """Minimal main function to reduce startup memory usage"""
    # Force garbage collection to start with a clean slate
    gc.collect()
    
    try:
        # Step 1: Initialize display with minimal overhead
        print("Initializing display...")
        display = initialise_display()
        
        # Step 2: Define constants after display init succeeds
        define_game_constants()
        
        # Step 3: Create game only after constants are defined
        print("Starting game...")
        gc.collect()  # Force collection before game creation
        game = PongGame(display)
        
        # Step 4: Simple game loop with basic error handling
        while True:
            try:
                # Update game with a try/except block
                gc.collect()
                game.update()
                time.sleep(GAME_DELAY)
                
                # Handle game over state
                if game.game_over:
                    time.sleep(2)
                    game.restart_game()
                    
            except MemoryError:
                # Simple error handling - just collect and continue
                print("Memory error - collecting garbage")
                gc.collect()
                time.sleep(0.5)
                
    except Exception as e:
        # Fatal error handling
        print(f"Error: {e}")
        gc.collect()
        time.sleep(1)


if __name__ == "__main__":
    # Extremely minimal startup - no nested try/except to reduce overhead
    gc.collect()
    main()

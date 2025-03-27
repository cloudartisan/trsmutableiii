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
BOTTOM_MARGIN = 20
CHAR_WIDTH = 6
LINE_HEIGHT = 15
GAME_DELAY = 0.1  # Main game loop delay

# Physical display configuration
SPI = board.SPI()
TFT_CS = board.D5  # Chip select pin
TFT_DC = board.D16  # Data/command pin
TFT_RESET = board.D9  # Reset pin

# Game characters
PADDLE_CHAR = '█'  # Paddle character (solid block for visibility)
BALL_CHAR = '●'    # Ball character
EMPTY_CHAR = ' '   # Empty space character
BORDER_CHAR = '═'  # Border character (horizontal bar)
NET_CHAR = '┊'    # Net character (dotted vertical line)

# Game board dimensions (in characters)
BOARD_WIDTH = 40
BOARD_HEIGHT = 16

# Game settings
PADDLE_SIZE = 3  # Shorter paddles (more challenging like original Pong)
PADDLE_SPEED = 1
MIN_BALL_DELAY = 2  # Faster initial ball delay (quicker gameplay)
MAX_BALL_DELAY = 2  
GAME_DELAY = 0.07   # Slightly slower for balanced movement speed
BALL_ACCELERATION = 0.85  # Ball speeds up during play but not as drastically
CPU_DIFFICULTY = 0.75  # 0.0 to 1.0, higher is more difficult
PLAYER_DIFFICULTY = 0.65  # Player AI is slightly worse than CPU
WINNING_SCORE = 11   # Score needed to win the game (original Pong used 11)


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

    debug_print(
        f"Display width: {display.width}",
        f"Display height: {display.height}",
        f"Display rotation: {display.rotation}"
    )
    return display


class PongGame:
    """Pong game implementation"""
    
    def __init__(self, display):
        self.display = display
        self.splash = displayio.Group()
        self.player_score = 0
        self.cpu_score = 0
        self.game_over = False
        self.winner = None
        
        # Set up paddles (left is player, right is CPU)
        self.player_y = (BOARD_HEIGHT - PADDLE_SIZE) // 2
        self.cpu_y = (BOARD_HEIGHT - PADDLE_SIZE) // 2
        
        # Set up ball
        self.ball_x = BOARD_WIDTH // 2
        self.ball_y = BOARD_HEIGHT // 2
        self.ball_dx = random.choice([-1, 1])
        self.ball_dy = random.choice([-1, 0, 1])
        self.ball_delay = MIN_BALL_DELAY
        self.frame_count = 0
        
        # Set up game state
        self.board = self.create_board()
    
    def create_board(self):
        """Create the initial game board"""
        # Create empty board
        board = [[EMPTY_CHAR for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        
        # Add paddles
        for i in range(PADDLE_SIZE):
            board[self.player_y + i][1] = PADDLE_CHAR  # Player paddle
            board[self.cpu_y + i][BOARD_WIDTH - 2] = PADDLE_CHAR  # CPU paddle
        
        # Add ball
        board[self.ball_y][self.ball_x] = BALL_CHAR
        
        return board
    
    def update_board(self):
        """Update the game board based on the current game state"""
        # Create empty board
        self.board = [[EMPTY_CHAR for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        
        # Add center net (like original Pong)
        center_x = BOARD_WIDTH // 2
        for y in range(BOARD_HEIGHT):
            if y % 2 == 0:  # Skip every other line for dashed effect
                self.board[y][center_x] = NET_CHAR
                
        # Add scores to the top of the game board (like original Pong)
        # Player score on left side - position more to the right so it's visible
        player_score_str = str(self.player_score)
        player_x = 10  # Fixed position to ensure visibility
        
        # CPU score on right side
        cpu_score_str = str(self.cpu_score)
        cpu_x = BOARD_WIDTH - 10  # Fixed position on the right side
        
        # Draw scores using block characters (like original Pong)
        # Define patterns for numbers 0-9 using block characters
        number_patterns = {
            0: [
                "███",
                "█ █",
                "█ █",
                "█ █",
                "███"
            ],
            1: [
                " █ ",
                "██ ",
                " █ ",
                " █ ",
                "███"
            ],
            2: [
                "███",
                "  █",
                "███",
                "█  ",
                "███"
            ],
            3: [
                "███",
                "  █",
                "███",
                "  █",
                "███"
            ],
            4: [
                "█ █",
                "█ █",
                "███",
                "  █",
                "  █"
            ],
            5: [
                "███",
                "█  ",
                "███",
                "  █",
                "███"
            ],
            6: [
                "███",
                "█  ",
                "███",
                "█ █",
                "███"
            ],
            7: [
                "███",
                "  █",
                "  █",
                "  █",
                "  █"
            ],
            8: [
                "███",
                "█ █",
                "███",
                "█ █",
                "███"
            ],
            9: [
                "███",
                "█ █",
                "███",
                "  █",
                "███"
            ]
        }
        
        # Draw player score (left side)
        player_digit = min(self.player_score, 9)  # Cap at 9 for simplicity
        pattern = number_patterns[player_digit]
        for row_idx, row in enumerate(pattern):
            for col_idx, char in enumerate(row):
                if char == '█':
                    self.board[row_idx + 1][player_x + col_idx] = PADDLE_CHAR
        
        # Draw CPU score (right side)
        cpu_digit = min(self.cpu_score, 9)  # Cap at 9 for simplicity
        pattern = number_patterns[cpu_digit]
        for row_idx, row in enumerate(pattern):
            for col_idx, char in enumerate(row):
                if char == '█':
                    self.board[row_idx + 1][cpu_x - len(row) + col_idx] = PADDLE_CHAR
        
        # Add paddles - make them shorter but wider (two columns)
        for i in range(PADDLE_SIZE):
            py = self.player_y + i
            cy = self.cpu_y + i
            if 0 <= py < BOARD_HEIGHT:
                self.board[py][1] = PADDLE_CHAR  # Player paddle
                self.board[py][2] = PADDLE_CHAR  # Make paddle wider
            if 0 <= cy < BOARD_HEIGHT:
                self.board[cy][BOARD_WIDTH - 3] = PADDLE_CHAR  # CPU paddle
                self.board[cy][BOARD_WIDTH - 2] = PADDLE_CHAR  # Make paddle wider
        
        # Add ball (only if game is not over)
        if not self.game_over and 0 <= self.ball_y < BOARD_HEIGHT and 0 <= self.ball_x < BOARD_WIDTH:
            self.board[self.ball_y][self.ball_x] = BALL_CHAR
    
    def move_ball(self):
        """Move the ball and handle collisions"""
        self.frame_count += 1
        
        # Only move the ball every ball_delay frames
        if self.frame_count < self.ball_delay:
            return
        
        self.frame_count = 0
        
        # Calculate new position - for diagonal movement, slow down horizontal movement to balance speed
        # This makes the ball move more naturally regardless of angle
        if self.ball_dy != 0:  # Ball is moving diagonally
            # Only move horizontally every other frame when moving diagonally
            if random.random() > 0.3:  # 70% chance to move horizontally during diagonal movement
                new_x = self.ball_x + self.ball_dx
            else:
                new_x = self.ball_x  # Don't move horizontally this frame
            new_y = self.ball_y + self.ball_dy
        else:  # Ball is moving horizontally
            new_x = self.ball_x + self.ball_dx
            new_y = self.ball_y
        
        # Handle top/bottom wall collisions
        if new_y < 0 or new_y >= BOARD_HEIGHT:
            self.ball_dy *= -1
            new_y = max(0, min(BOARD_HEIGHT - 1, new_y))
        
        # Handle paddle collisions - authentic Pong behavior
        if (new_x == 1 or new_x == 2) and self.player_y <= new_y < self.player_y + PADDLE_SIZE:
            # Player paddle collision
            self.ball_dx = 1
            
            # Original Pong divided the paddle into sections for different return angles
            # The further from center, the more extreme the angle
            relative_hit = new_y - self.player_y  # Position where ball hit paddle (0 to PADDLE_SIZE-1)
            segment = relative_hit / (PADDLE_SIZE - 1)  # Normalized to 0.0 - 1.0
            
            # Center is straight, edges give angled returns
            if segment < 0.2:  # Top 20% - sharp upward angle
                self.ball_dy = -1
            elif segment < 0.4:  # Upper-middle - slight upward angle
                self.ball_dy = -1
            elif segment > 0.8:  # Bottom 20% - sharp downward angle
                self.ball_dy = 1
            elif segment > 0.6:  # Lower-middle - slight downward angle
                self.ball_dy = 1
            else:  # Center - straight return
                self.ball_dy = 0
            
            # Speed up the ball each time it hits a paddle (authentic Pong behavior)
            self.ball_delay = max(1, int(self.ball_delay * BALL_ACCELERATION))
                
        elif (new_x == BOARD_WIDTH - 2 or new_x == BOARD_WIDTH - 3) and self.cpu_y <= new_y < self.cpu_y + PADDLE_SIZE:
            # CPU paddle collision
            self.ball_dx = -1
            
            # Same angle calculation logic as player paddle
            relative_hit = new_y - self.cpu_y 
            segment = relative_hit / (PADDLE_SIZE - 1)
            
            if segment < 0.2:
                self.ball_dy = -1
            elif segment < 0.4:
                self.ball_dy = -1
            elif segment > 0.8:
                self.ball_dy = 1
            elif segment > 0.6:
                self.ball_dy = 1
            else:
                self.ball_dy = 0
            
            # Speed up the ball each time it hits a paddle
            self.ball_delay = max(1, int(self.ball_delay * BALL_ACCELERATION))
        
        # Handle scoring
        if new_x < 0:
            # CPU scores
            self.cpu_score += 1
            self.reset_ball()
            return
        elif new_x >= BOARD_WIDTH:
            # Player scores
            self.player_score += 1
            self.reset_ball()
            return
        
        # Update ball position
        self.ball_x = new_x
        self.ball_y = new_y
        
        # Check for game over
        if self.player_score >= WINNING_SCORE:
            self.game_over = True
            self.winner = "PLAYER"
        elif self.cpu_score >= WINNING_SCORE:
            self.game_over = True
            self.winner = "CPU"
    
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
        """Move the CPU's paddle based on AI difficulty"""
        # AI randomly decides whether to move optimally or not based on difficulty
        if random.random() < CPU_DIFFICULTY:
            # Move optimally
            paddle_middle = self.cpu_y + PADDLE_SIZE // 2
            if self.ball_dx > 0:  # Only track the ball if it's moving toward the CPU
                # Original Pong paddles couldn't reach the top of the screen
                # This was an intentional limitation Alcorn kept in the game
                if paddle_middle < self.ball_y and self.cpu_y + PADDLE_SIZE < BOARD_HEIGHT:
                    self.cpu_y += PADDLE_SPEED
                elif paddle_middle > self.ball_y and self.cpu_y > 1:  # Can't reach very top
                    self.cpu_y -= PADDLE_SPEED
        else:
            # Move randomly or not at all
            move = random.choice([-1, 0, 1])
            if move == -1 and self.cpu_y > 1:  # Can't reach very top
                self.cpu_y -= PADDLE_SPEED
            elif move == 1 and self.cpu_y + PADDLE_SIZE < BOARD_HEIGHT:
                self.cpu_y += PADDLE_SPEED
    
    def simulate_player_move(self):
        """Simulate player paddle movement for automatic play with imperfection"""
        # AI randomly decides whether to move optimally or make a mistake
        if random.random() < PLAYER_DIFFICULTY:
            # Move optimally
            paddle_middle = self.player_y + PADDLE_SIZE // 2
            
            # Only move if the ball is moving towards the player
            if self.ball_dx < 0:
                # Original Pong paddles couldn't reach the top of the screen
                # This was an intentional limitation Alcorn kept in the game
                if paddle_middle < self.ball_y and self.player_y + PADDLE_SIZE < BOARD_HEIGHT:
                    self.move_player_paddle(1)  # Move down
                elif paddle_middle > self.ball_y and self.player_y > 1:  # Can't reach very top
                    self.move_player_paddle(-1)  # Move up
        else:
            # Make a mistake: move randomly or not at all
            if self.ball_dx < 0:  # Only consider moving if ball is coming toward player
                move = random.choice([-1, 0, 1])
                if move == -1 and self.player_y > 1:  # Can't reach very top
                    self.move_player_paddle(-1)  # Move up
                elif move == 1 and self.player_y + PADDLE_SIZE < BOARD_HEIGHT:
                    self.move_player_paddle(1)  # Move down
    
    def display_game(self):
        """Display the current game state on the screen"""
        splash = displayio.Group()
        self.display.show(splash)
        
        # Scores are now drawn directly in the game board using block characters
        # No need for separate score labels anymore
        
        # Display game board with border
        border_line = BORDER_CHAR * BOARD_WIDTH
        top_border = label.Label(
            terminalio.FONT,
            text=border_line,
            x=LEFT_MARGIN,
            y=TOP_MARGIN - LINE_HEIGHT,
            color=0xFFFFFF  # White color
        )
        splash.append(top_border)
        
        bottom_border = label.Label(
            terminalio.FONT,
            text=border_line,
            x=LEFT_MARGIN,
            y=TOP_MARGIN + BOARD_HEIGHT * LINE_HEIGHT,
            color=0xFFFFFF  # White color
        )
        splash.append(bottom_border)
        
        # Display game board
        for y, row in enumerate(self.board):
            line = ''.join(row)
            row_area = label.Label(
                terminalio.FONT,
                text=line,
                x=LEFT_MARGIN,
                y=TOP_MARGIN + y * LINE_HEIGHT,
                color=0x00FF00  # Green color
            )
            splash.append(row_area)
        
        # Display game over message if needed
        if self.game_over:
            message = f"{self.winner} WINS!"
            message_area = label.Label(
                terminalio.FONT,
                text=message,
                x=(DISPLAY_WIDTH - len(message) * CHAR_WIDTH) // 2,
                y=TOP_MARGIN + (BOARD_HEIGHT + 2) * LINE_HEIGHT,
                color=0xFFFF00  # Yellow color
            )
            splash.append(message_area)
            restart_text = "RESTARTING..."
            restart_area = label.Label(
                terminalio.FONT,
                text=restart_text,
                x=(DISPLAY_WIDTH - len(restart_text) * CHAR_WIDTH) // 2,
                y=TOP_MARGIN + (BOARD_HEIGHT + 4) * LINE_HEIGHT,
                color=0xFFFF00  # Yellow color
            )
            splash.append(restart_area)
    
    def update(self):
        """Update the game state"""
        if not self.game_over:
            # Move the ball
            self.move_ball()
            
            # Move the CPU paddle
            self.move_cpu_paddle()
            
            # Simulate player movement (in absence of keyboard)
            self.simulate_player_move()
            
            # Update the board representation
            self.update_board()
        
        # Display the updated game
        self.display_game()
    
    def restart_game(self):
        """Restart the game"""
        self.player_score = 0
        self.cpu_score = 0
        self.game_over = False
        self.winner = None
        self.player_y = (BOARD_HEIGHT - PADDLE_SIZE) // 2
        self.cpu_y = (BOARD_HEIGHT - PADDLE_SIZE) // 2
        self.reset_ball()
        self.update_board()


def main():
    """Main function to run the Pong game"""
    display = initialise_display()
    game = PongGame(display)
    
    # Display title screen
    splash = displayio.Group()
    display.show(splash)
    
    title = label.Label(
        terminalio.FONT,
        text="PONG",
        scale=3,
        x=DISPLAY_WIDTH // 2 - 30,
        y=DISPLAY_HEIGHT // 3,
        color=0xFFFFFF  # White color
    )
    splash.append(title)
    
    subtitle = label.Label(
        terminalio.FONT,
        text="TRS-80 MODEL III EDITION",
        x=DISPLAY_WIDTH // 2 - 100,
        y=DISPLAY_HEIGHT // 2,
        color=0x00FF00  # Green color
    )
    splash.append(subtitle)
    
    instructions = label.Label(
        terminalio.FONT,
        text="AUTO-PLAY MODE",
        x=DISPLAY_WIDTH // 2 - 60,
        y=DISPLAY_HEIGHT // 2 + 40,
        color=0xFFFF00  # Yellow color
    )
    splash.append(instructions)
    
    start_text = label.Label(
        terminalio.FONT,
        text="STARTING IN 3 SECONDS...",
        x=DISPLAY_WIDTH // 2 - 90,
        y=DISPLAY_HEIGHT // 2 + 70,
        color=0xFFFF00  # Yellow color
    )
    splash.append(start_text)
    
    time.sleep(3)
    
    # Main game loop
    try:
        while True:
            game.update()
            time.sleep(GAME_DELAY)  # Use the faster game delay
            
            # If game is over, wait a bit and restart
            if game.game_over:
                time.sleep(3)
                game.restart_game()
    except KeyboardInterrupt:
        print("Game terminated by user")


if __name__ == "__main__":
    main()

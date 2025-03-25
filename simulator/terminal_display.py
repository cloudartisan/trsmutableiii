"""
Terminal-based display simulator for CircuitPython display code.
This renders CircuitPython display actions to the terminal.
"""
import os
import sys
import time
import threading
from collections import defaultdict

from .circuitpython_mock import display_events


class TerminalDisplaySimulator:
    """Renders CircuitPython display actions to the terminal."""
    
    def __init__(self, width=80, height=24, char_width=6, line_height=15):
        """Initialize the terminal display simulator.
        
        Args:
            width (int): Width of the terminal display in characters
            height (int): Height of the terminal display in characters
            char_width (int): Width of each character in pixels (for conversion)
            line_height (int): Height of each line in pixels (for conversion)
        """
        self.width = width
        self.height = height
        self.char_width = char_width
        self.line_height = line_height
        
        # Create a buffer to store the display content
        self.buffer = [[' ' for _ in range(width)] for _ in range(height)]
        
        # Map to store text elements by position (y, x)
        self.text_elements = {}
        
        # Keep track of the current display group
        self.current_group = None
        
        # Initial render
        self._render()
        
        # Start the event monitoring thread
        self.running = True
        self.event_thread = threading.Thread(target=self._monitor_events)
        self.event_thread.daemon = True
        self.event_thread.start()
    
    def _monitor_events(self):
        """Monitor display events and update the terminal."""
        last_event_count = 0
        
        while self.running:
            # Check if there are new events
            if len(display_events) > last_event_count:
                for i in range(last_event_count, len(display_events)):
                    self._process_event(display_events[i])
                last_event_count = len(display_events)
                self._render()
            
            time.sleep(0.1)  # Check for events every 100ms
    
    def _process_event(self, event):
        """Process a display event."""
        event_type, data = event
        
        if event_type == 'create_label':
            _, text, x, y, _, _ = data
            # Only add non-empty text
            if text:
                self._add_text(text, x, y)
                # Debug output
                # print(f"Label created: '{text}' at ({x}, {y})")
        
        elif event_type == 'update_text':
            # A label's text was updated
            label_obj, text = data
            if text and hasattr(label_obj, 'x') and hasattr(label_obj, 'y'):
                self._add_text(text, label_obj.x, label_obj.y)
                # Debug output
                # print(f"Text updated: '{text}' at ({label_obj.x}, {label_obj.y})")
        
        elif event_type == 'show':
            # In the updated code, show event now contains (group, group_counter)
            group, group_id = data
            
            # Always clear the display for a new show event - each show is a new screen
            self._clear_buffer()
            self._render()  # Force immediate render of the cleared display
            
            # Update our reference to the current group
            if self.current_group != group:
                # This indicates a completely new group (like after clear_display)
                self.current_group = group
                print(f"Display cleared - showing group #{group_id}")
            
            # Extract and show text elements from the group
            if hasattr(group, 'children'):
                for child in group.children:
                    if hasattr(child, 'text') and hasattr(child, 'x') and hasattr(child, 'y') and child.text:
                        self._add_text(child.text, child.x, child.y)
        
        elif event_type == 'append':
            # An item was appended to a group
            item = data
            if hasattr(item, 'text') and hasattr(item, 'x') and hasattr(item, 'y'):
                self._add_text(item.text, item.x, item.y)
                # Debug output
                # print(f"Appended: '{item.text}' at ({item.x}, {item.y})")
    
    def _add_text(self, text, x, y):
        """Add text to the buffer at the specified position."""
        # Convert pixel position to character position based on constants
        display_width = 280  # Physical display width
        
        # Calculate terminal coordinates
        term_x = int((x / display_width) * self.width)
        
        # Simply divide by 15 (the LINE_HEIGHT from code.py) and floor
        # This consistently maps each block of 15 pixels to a single terminal line
        term_y = y // 15  # Integer division
        
        # Store the text element
        self.text_elements[(term_y, term_x)] = text
        
        # Update the buffer
        for i, char in enumerate(text):
            if 0 <= term_y < self.height and 0 <= term_x + i < self.width:
                self.buffer[term_y][term_x + i] = char
    
    def _clear_buffer(self):
        """Clear the display buffer."""
        self.buffer = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        self.text_elements = {}
    
    def force_clear(self):
        """Force clear the display and render immediately."""
        self._clear_buffer()
        self._render()  # Immediately render the cleared display
    
    def _render(self):
        """Render the display to the terminal."""
        # Clear the terminal - use ANSI escape sequence to fully clear and reset cursor position
        print("\033[2J\033[H", end="")  # Clear entire screen and move cursor to home position
        
        # Print header with instructions
        print("\033[1;36m=== TRS-80 Model III Simulator ===\033[0m")
        print("Press Ctrl+C to exit")
        print()
        
        # Print the top border
        print("\033[1;34m┌" + "─" * self.width + "┐\033[0m")
        
        # Print each line of the buffer
        for row in self.buffer:
            print("\033[1;34m│\033[0m" + "\033[1;36m" + "".join(row) + "\033[0m" + "\033[1;34m│\033[0m")
        
        # Print the bottom border
        print("\033[1;34m└" + "─" * self.width + "┘\033[0m")
        
        # Force flush stdout to ensure immediate display
        sys.stdout.flush()
    
    def stop(self):
        """Stop the event monitoring thread."""
        self.running = False
        if self.event_thread.is_alive():
            self.event_thread.join(timeout=1.0)


def create_simulator():
    """Create and return a terminal display simulator."""
    return TerminalDisplaySimulator()

# Global reference to the current simulator
current_simulator = None

def get_current_simulator():
    """Get the current simulator instance."""
    return current_simulator

def set_current_simulator(simulator):
    """Set the current simulator instance."""
    global current_simulator
    current_simulator = simulator

def force_clear_display():
    """Force the display to clear immediately."""
    if current_simulator:
        current_simulator.force_clear()
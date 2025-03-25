"""
Program runner for CircuitPython programs on the TRS-80 Model III simulator.
This allows running any program in the simulator environment.
"""
import os
import sys
import json
import time
import importlib.util
import importlib.machinery
import types

# Import the mock modules first to ensure they're set up before program code runs
from .circuitpython_mock import clear_events
from .terminal_display import create_simulator, set_current_simulator, force_clear_display


class ProgramRunner:
    """Runs CircuitPython programs in the simulator environment."""
    
    def __init__(self, program_path=None):
        """Initialize the program runner.
        
        Args:
            program_path (str): Path to the program directory to run (containing code.py)
        """
        self.program_path = program_path
        self.module_name = os.path.basename(program_path) if program_path else None
        self.simulator = None
    
    def run(self, program_path=None):
        """Run a CircuitPython program in the simulator.
        
        Args:
            program_path (str, optional): Path to the program directory to run (containing code.py)
        
        Returns:
            bool: True if successful, False if there was an error
        """
        if program_path:
            self.program_path = program_path
            self.module_name = os.path.basename(program_path)
        
        if not self.program_path:
            print("Error: No program path specified")
            return False
        
        # Reset any previous state
        clear_events()
        
        # Create the terminal simulator
        self.simulator = create_simulator()
        # Set it as the current simulator
        set_current_simulator(self.simulator)
        
        try:
            # Load the program module
            code_path = os.path.join(self.program_path, 'code.py')
            if not os.path.exists(code_path):
                print(f"Error: code.py not found in {self.program_path}")
                return False
            
            # Add the program directory to the path so relative imports work
            if self.program_path not in sys.path:
                sys.path.insert(0, self.program_path)
            
            # Create a parent package for relative imports
            parent_pkg = types.ModuleType(self.module_name)
            sys.modules[self.module_name] = parent_pkg
            parent_pkg.__path__ = [self.program_path]
            
            # Load all Python files in the program directory as modules
            for file_name in os.listdir(self.program_path):
                if file_name.endswith('.py') and file_name != 'code.py':
                    module_name = file_name[:-3]  # Remove .py extension
                    full_module_name = f"{self.module_name}.{module_name}"
                    
                    # Skip if already loaded
                    if full_module_name in sys.modules:
                        continue
                    
                    # Load the module
                    module_path = os.path.join(self.program_path, file_name)
                    try:
                        spec = importlib.util.spec_from_file_location(full_module_name, module_path)
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[full_module_name] = module
                        spec.loader.exec_module(module)
                    except Exception as e:
                        print(f"Warning: Failed to load module {full_module_name}: {e}")
            
            # Now load and execute the main code.py file
            print(f"Running {code_path}...")
            
            # Read the file content directly
            with open(code_path, 'r') as f:
                code_content = f.read()
            
            # Replace relative imports with absolute imports
            code_content = code_content.replace("from .utils", f"from {self.module_name}.utils")
            code_content = code_content.replace("from . import", f"from {self.module_name} import")
            
            # Fix adafruit display_text import for all programs
            code_content = code_content.replace("from adafruit_display_text import label", 
                                               "# Fix for simulator\nlabel = sys.modules['adafruit_display_text.label']")
            
            # We'll handle clear_display patching below
            
            # For wargames, patch the clear_display function and screens.json path
            if self.module_name == 'wargames':
                # We'll handle clearing events directly in the patched clear_display function
                # No need to patch debug_print anymore
                
                # We no longer need to patch display_line_with_typing for debugging
                
                # Patch the clear_display function to force display clearing
                clear_display_replacement = """def clear_display(display):
    \"\"\"Clear the display and return a new Group.\"\"\"
    debug_print("Clearing display...")
    
    # Force clear the display in simulator mode
    try:
        from simulator.terminal_display import force_clear_display
        force_clear_display()
    except ImportError:
        pass  # Not running in simulator
    
    # Create a new display group
    splash = displayio.Group()
    display.show(splash)
    gc.collect()  # Explicitly collect garbage after clearing display
    return splash"""
                
                # Replace the clear_display function with our patched version
                code_content = code_content.replace("def clear_display(display):", clear_display_replacement)
                
                # Patch the format_and_display_line function to handle blank lines properly
                format_and_display_line_replacement = """def format_and_display_line(display, splash, left_text, centre_text, right_text, y, scale, colour, upper_delay, lower_delay):
    \"\"\"Format and display a line with left, centre, and right alignment\"\"\"
    # For intentionally blank lines, still advance the y position and render a space
    # This preserves intentional blank lines in the screens.json
    is_blank_line = not left_text and not centre_text and not right_text
    
    total_chars = (display.width - LEFT_MARGIN - RIGHT_MARGIN) // CHAR_WIDTH
    
    # Handle completely blank lines differently
    if is_blank_line:
        # Just display a single space to advance the line but not show anything
        y = display_line_with_typing(splash, " ", LEFT_MARGIN, y, scale, colour, upper_delay, lower_delay)
        return y
        
    # Process normal lines with content
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

    return y"""

                # Patch the display_screen_with_typing function to ensure display clearing
                display_screen_replacement = """def display_screen_with_typing(display, screen):
    \"\"\"Display all lines of a screen with a typing effect\"\"\"
    debug_print("Displaying screen with typing effect")
    
    # Force clear the display in simulator mode at the beginning of each screen
    try:
        from simulator.terminal_display import force_clear_display
        force_clear_display()
    except ImportError:
        pass  # Not running in simulator
    
    splash = clear_display(display)

    lines = screen["lines"]
    scale = screen.get("scale", FONT_SCALE)
    colour = tuple(screen.get("colour", DEFAULT_TEXT_COLOUR))
    upper_delay = screen.get("upper_delay", DEFAULT_UPPER_DELAY)
    lower_delay = screen.get("lower_delay", DEFAULT_LOWER_DELAY)
    line_delays = screen.get("line_delays", {})
    y = TOP_MARGIN"""
                
                # Patch the screens.json path
                code_content = code_content.replace("'./screens.json'", 
                                                  f"'{os.path.join(self.program_path, 'screens.json')}'")
                code_content = code_content.replace("\"./screens.json\"", 
                                                  f"\"{os.path.join(self.program_path, 'screens.json')}\"")
                                                  
                # Replace only necessary functions
                code_content = code_content.replace("def format_and_display_line(display, splash, left_text, centre_text, right_text, y, scale, colour, upper_delay, lower_delay):", format_and_display_line_replacement)
                code_content = code_content.replace("def display_screen_with_typing(display, screen):", display_screen_replacement)
                
                print(f"Patched wargames code for simulation")
            
            # Create a namespace for execution with all required modules
            code_namespace = {
                "__name__": self.module_name,
                "__file__": code_path,
                "__package__": self.module_name,
                "board": sys.modules['board'],
                "displayio": sys.modules['displayio'],
                "terminalio": sys.modules['terminalio'],
                "adafruit_display_text": sys.modules['adafruit_display_text'],
                "adafruit_display_text.label": sys.modules['adafruit_display_text.label'],
                "label": sys.modules['adafruit_display_text.label'],
                "ST7789": sys.modules['adafruit_st7789'].ST7789,
                "adafruit_st7789": sys.modules['adafruit_st7789'],
                "time": time,
                "json": json,
                "os": os,
                "sys": sys,
                "gc": sys.modules['gc'],
            }
            
            # Add utils module for wargames
            if self.module_name == 'wargames' and 'wargames.utils' in sys.modules:
                code_namespace['wrap_text'] = sys.modules['wargames.utils'].wrap_text
            
            # Add sleep hack to slow down the simulation for wargames
            if self.module_name == 'wargames':
                # Make the simulation more visible by reducing the speed
                code_content = code_content.replace("DEFAULT_CHAR_DELAY=0.025", "DEFAULT_CHAR_DELAY=0.01")
                code_content = code_content.replace("DEFAULT_LOWER_DELAY=0.25", "DEFAULT_LOWER_DELAY=0.05")
                code_content = code_content.replace("DEFAULT_UPPER_DELAY=0.005", "DEFAULT_UPPER_DELAY=0.01")
                code_content = code_content.replace("DEFAULT_SCREEN_DELAY=4", "DEFAULT_SCREEN_DELAY=2")
            
            # Execute the code
            print("Executing code...")
            exec(code_content, code_namespace)
            
            # If it has a main function, call it
            if 'main' in code_namespace:
                print("Found main() function, calling it...")
                code_namespace['main']()
            else:
                print("No main() function found. Code has been executed.")
            
            print("\nProgram running in simulator. Press Ctrl+C to exit.")
            
            # Keep the program running until interrupted
            try:
                while True:
                    pass
            except KeyboardInterrupt:
                print("\nProgram interrupted by user")
            
            return True
            
        except Exception as e:
            print(f"Error running program: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Clean up
            if self.simulator:
                self.simulator.stop()


def run_program(program_path):
    """Run a CircuitPython program in the simulator.
    
    Args:
        program_path (str): Path to the program directory to run (containing code.py)
    
    Returns:
        bool: True if successful, False if there was an error
    """
    runner = ProgramRunner()
    return runner.run(program_path)
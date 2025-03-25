"""
Mocks for CircuitPython libraries.
These mocks allow CircuitPython code to run on a regular computer.
"""
import sys
import time
import types
from collections import defaultdict

# Keep track of all mocked hardware events
display_events = []
pin_states = defaultdict(lambda: False)
spi_transfers = []

class Board:
    """Mock for board module with common pins."""
    
    # Standard pins
    D5 = "D5"   # Chip select pin
    D9 = "D9"   # Reset pin 
    D16 = "D16" # Data/command pin
    TX = "TX"
    RX = "RX"
    SCL = "SCL"
    SDA = "SDA"
    SCK = "SCK"
    MOSI = "MOSI"
    MISO = "MISO"
    
    # Board identification
    board_id = "Mock QT Py ESP32-S3"
    
    @staticmethod
    def SPI():
        """Create a mock SPI interface."""
        return SPI()
    
    @staticmethod
    def I2C():
        """Create a mock I2C interface."""
        return I2C()


class DisplayIO:
    """Mock for displayio module."""
    
    class Group:
        """A group of display elements."""
        def __init__(self):
            self.children = []
        
        def append(self, item):
            """Add an item to the group."""
            self.children.append(item)
            # Record the event
            display_events.append(('append', item))
    
    class FourWire:
        """Mock for FourWire display protocol."""
        def __init__(self, spi, command, chip_select, reset=None):
            self.spi = spi
            self.command_pin = command
            self.chip_select = chip_select
            self.reset_pin = reset
            display_events.append(('init_fourwire', (spi, command, chip_select, reset)))
    
    @staticmethod
    def release_displays():
        """Release all displays."""
        display_events.append(('release_displays', None))


class MockLabel:
    """Mock for adafruit_display_text.label."""
    
    @staticmethod
    def Label(font, text="", x=0, y=0, scale=1, color=0xFFFFFF):
        """Create a new label."""
        label = LabelObject(font, text, x, y, scale, color)
        display_events.append(('create_label', (font, text, x, y, scale, color)))
        return label


class LabelObject:
    """An actual label object."""
    def __init__(self, font, text="", x=0, y=0, scale=1, color=0xFFFFFF):
        self.font = font
        self._text = text
        self.x = x
        self.y = y
        self.scale = scale
        self.color = color
        
        # Log creation if there's text
        if text:
            display_events.append(('update_text', (self, text)))
    
    @property
    def text(self):
        return self._text
    
    @text.setter
    def text(self, value):
        # Record the text change event when text is modified
        if value != self._text:
            display_events.append(('update_text', (self, value)))
            self._text = value


class TerminalIO:
    """Mock for terminalio module."""
    class FONT:
        """Mock for the built-in font."""
        pass


class SPI:
    """Mock for SPI interface."""
    def __init__(self):
        self.frequency = 24000000  # Default frequency
        display_events.append(('init_spi', None))
    
    def configure(self, baudrate=None, polarity=0, phase=0):
        """Configure the SPI bus."""
        if baudrate is not None:
            self.frequency = baudrate
        display_events.append(('configure_spi', (baudrate, polarity, phase)))
    
    def write(self, buf):
        """Write to the SPI bus."""
        spi_transfers.append(('write', buf))
        return len(buf)
    
    def readinto(self, buf):
        """Read from the SPI bus into a buffer."""
        spi_transfers.append(('readinto', buf))
        return len(buf)


class I2C:
    """Mock for I2C interface."""
    def __init__(self):
        self.frequency = 100000  # Default frequency
        display_events.append(('init_i2c', None))
    
    def scan(self):
        """Scan for I2C devices."""
        return [0x3C]  # Return a common display address
    
    def writeto(self, address, buf):
        """Write to an I2C device."""
        display_events.append(('i2c_write', (address, buf)))
        return len(buf)
    
    def readfrom_into(self, address, buf):
        """Read from an I2C device into a buffer."""
        display_events.append(('i2c_read', (address, buf)))
        return len(buf)


class ST7789:
    """Mock for ST7789 display."""
    def __init__(self, bus, width, height, colstart=0, rowstart=0, rotation=0):
        self.bus = bus
        self.width = width
        self.height = height
        self.colstart = colstart
        self.rowstart = rowstart
        self.rotation = rotation
        self.current_group = None
        self.group_counter = 0  # Track unique groups
        display_events.append(('init_st7789', (width, height, colstart, rowstart, rotation)))
    
    def show(self, group):
        """Show a displayio Group."""
        # Mark this as a new group with a unique ID
        self.group_counter += 1
        
        # Store the current group and dispatch the show event
        self.current_group = group
        display_events.append(('show', (group, self.group_counter)))


class DigitalInOut:
    """Mock for digitalio.DigitalInOut."""
    def __init__(self, pin):
        self.pin = pin
        self.direction = None
        self.value = False
        display_events.append(('init_pin', pin))
    
    def switch_to_output(self, value=False):
        """Switch the pin to output mode."""
        self.direction = 'output'
        self.value = value
        pin_states[self.pin] = value
        display_events.append(('pin_to_output', (self.pin, value)))
    
    def switch_to_input(self, pull=None):
        """Switch the pin to input mode."""
        self.direction = 'input'
        display_events.append(('pin_to_input', (self.pin, pull)))


class Direction:
    """Mock for digitalio.Direction."""
    INPUT = 'input'
    OUTPUT = 'output'


class Pull:
    """Mock for digitalio.Pull."""
    UP = 'up'
    DOWN = 'down'


def create_mock_modules():
    """Create and install all the mock modules."""
    modules = {
        'board': Board,
        'displayio': DisplayIO,
        'terminalio': TerminalIO,
        'adafruit_display_text.label': MockLabel,
        'adafruit_display_text': types.ModuleType('adafruit_display_text'),
        'adafruit_st7789': types.ModuleType('adafruit_st7789'),
        'digitalio': types.ModuleType('digitalio'),
        'gc': types.ModuleType('gc'),
    }
    
    # Add the mock modules to sys.modules
    for name, mod in modules.items():
        if isinstance(mod, type) or callable(mod):
            module = types.ModuleType(name)
            for attr_name in dir(mod):
                if not attr_name.startswith('__'):
                    attr = getattr(mod, attr_name)
                    setattr(module, attr_name, attr)
            sys.modules[name] = module
        else:
            sys.modules[name] = mod
    
    # Special cases for specific modules
    sys.modules['adafruit_st7789'].ST7789 = ST7789
    sys.modules['digitalio'].DigitalInOut = DigitalInOut
    sys.modules['digitalio'].Direction = Direction
    sys.modules['digitalio'].Pull = Pull
    sys.modules['gc'].collect = lambda: None
    sys.modules['adafruit_display_text'].label = sys.modules['adafruit_display_text.label']


def clear_events():
    """Clear all recorded hardware events."""
    display_events.clear()
    pin_states.clear()
    spi_transfers.clear()


# Install the mocks when this module is imported
create_mock_modules()
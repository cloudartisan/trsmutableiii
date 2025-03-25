import board
import displayio
import terminalio
import time
from adafruit_display_text import label
from adafruit_st7789 import ST7789

# Initialize display
spi = board.SPI()
tft_cs = board.D5
tft_dc = board.D16
tft_reset = board.D9

display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=tft_reset)
display = ST7789(display_bus, width=280, height=240, rowstart=20, rotation=270)

# Function to display text with a delay
def display_text(splash, text, x, y, delay=0.5):
    text_area = label.Label(terminalio.FONT, text=text, color=0x00FF00, x=x, y=y)
    splash.append(text_area)
    display.show(splash)
    time.sleep(delay)

# Boot sequence simulation
def trs80_boot_sequence():
    splash = displayio.Group()
    display.show(splash)
    
    # Blank screen at startup
    time.sleep(1)

    # Simulate memory test
    memory_test = "****   MEMORY SIZE = 48K   ****"
    display_text(splash, memory_test, 10, 50, delay=2)
    
    # Simulate system initialization and disk booting
    for i in range(0, 5):
        display_text(splash, "-", 100 + i * 20, 100, delay=0.2)
    
    # Display the TRSDOS boot success message or error prompt
    splash = displayio.Group()  # Clear previous content
    display.show(splash)
    display_text(splash, "TRSDOS Ready", 10, 100, delay=3)
    display_text(splash, "Cass?", 10, 140)

# Run the boot sequence
trs80_boot_sequence()
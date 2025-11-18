from machine import I2C, Pin
import time
from i2c_lcd import I2cLcd

# ---------- I2C1 setup ----------
# Wiring: VCC→5V, GND→GND, SDA→GP14, SCL→GP15
i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=100_000)

# Detect LCD address (usually 0x27 or 0x3F)
addrs = i2c.scan()
if not addrs:
    raise RuntimeError("No I2C devices found. Check wiring.")
candidates = [a for a in addrs if (0x20 <= a <= 0x27) or (0x38 <= a <= 0x3F)]
lcd_addr = candidates[0] if candidates else addrs[0]

# ---------- LCD setup ----------
ROWS, COLS = 4, 20
lcd = I2cLcd(i2c, lcd_addr, ROWS, COLS)

# --- compatibility helpers (handles putstr/move_to or write/set_cursor) ---
def _cursor(col, row):
    if hasattr(lcd, "move_to"):
        lcd.move_to(col, row)
    elif hasattr(lcd, "set_cursor"):
        lcd.set_cursor(col, row)

def _write(text):
    if hasattr(lcd, "putstr"):
        lcd.putstr(text)
    elif hasattr(lcd, "write"):
        lcd.write(text)

def _print_at(col, row, text, pad_to=None):
    if pad_to is not None:
        text = (text + " " * pad_to)[:pad_to]
    _cursor(col, row)
    _write(text)

# ---------- Boot screen ----------
lcd.clear()
_print_at(0, 0, "Pico I2C LCD Ready")
_print_at(0, 1, f"Addr: 0x{lcd_addr:02x}")
_print_at(0, 2, "Using I2C1 (GP14,15)")
time.sleep(2)
lcd.clear()

# ---------- Live counter ----------
count = 0
spinner = ["|", "/", "-", "\\"]
spin_idx = 0

_print_at(0, 0, "Live Counter Demo")
_print_at(0, 1, "Press Ctrl+C to stop")

try:
    last_update = time.ticks_ms()
    while True:
        now = time.ticks_ms()
        if time.ticks_diff(now, last_update) >= 1000:
            last_update = now
            count += 1
            _print_at(0, 2, f"Count: {count}", pad_to=COLS)
        spin = spinner[spin_idx]
        spin_idx = (spin_idx + 1) % len(spinner)
        _print_at(COLS - 3, 3, f"{spin}  ")
        time.sleep(0.15)

except KeyboardInterrupt:
    _print_at(0, 3, "Stopped by user", pad_to=COLS)
    time.sleep(1)
    lcd.clear()


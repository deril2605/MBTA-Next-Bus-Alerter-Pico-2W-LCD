import network, time, json
from machine import I2C, Pin
from machine_i2c_lcd import I2cLcd   # IMPORTANT: Using your driver!

try:
    import urequests as requests
except:
    import requests

# ------------ WIFI ------------
WIFI_SSID = ""
WIFI_PW   = ""

# ------------ MBTA CONFIG ------------
BUS_ROUTE_ID    = "116"
BUS_STOP_ID     = "5733"
BUS_DIR_ID      = "1"     # inbound

BLUE_ROUTE_ID   = "Blue"
BLUE_STOP_ID    = "place-aport"
BLUE_DIR_ID     = "0"     # inbound for blue line (you set this)

API_KEY = "fd7a24507d4e45208098234176abc0b7"

# ------------ NIGHT MODE WINDOW ------------
NIGHT_START = 23   # 11 PM
NIGHT_END   = 6    # 6 AM

def in_night_mode():
    """Return True if current time is between 23:00 and 06:00."""
    hour = time.localtime()[3]
    # Night is 23, 0, 1, 2, 3, 4, 5
    return (hour >= NIGHT_START) or (hour < NIGHT_END)

# ------------ LCD SETUP (I2C1 GP14/GP15) ------------
i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=100_000)
addr = (i2c.scan() or [0x27])[0]
lcd = I2cLcd(i2c, addr, 4, 20)

# ------------ CUSTOM ICONS ------------

# Bell (for BLUE LINE)
bell_icon = bytearray([
    0x04,
    0x0E,
    0x0A,
    0x0A,
    0x0A,
    0x1F,
    0x00,
    0x04
])

# Speaker (for BUS)
speaker_icon = bytearray([
    0x01,
    0x03,
    0x07,
    0x1F,
    0x1F,
    0x07,
    0x03,
    0x01
])

# Load icons to CGRAM
lcd.custom_char(0, speaker_icon)  # index 0
lcd.custom_char(1, bell_icon)     # index 1

# ------------ HELPERS ------------
def mv(c, r):
    lcd.move_to(c, r)

def put(s):
    lcd.putstr(s)

def minutes_until(iso_str):
    try:
        date, clock = iso_str.split("T")
        y, m, d = map(int, date.split("-"))
        clock = clock.split("-")[0].split("+")[0]
        hh, mm, ss = map(int, clock.split(":"))
        target = time.mktime((y, m, d, hh, mm, ss, 0, 0))
        now = time.time()
        return int((target - now) / 60)
    except:
        return None

def fetch_predictions(route, stop, direction=None):
    url = (
        "https://api-v3.mbta.com/predictions"
        f"?filter[route]={route}"
        f"&filter[stop]={stop}"
        "&sort=departure_time"
        "&page[limit]=4"
        "&fields[prediction]=departure_time"
    )
    if direction is not None:
        url += f"&filter[direction_id]={direction}"

    headers = {"accept": "application/json"}
    if API_KEY:
        headers["x-api-key"] = API_KEY

    r = requests.get(url, headers=headers)
    try:
        data = r.json()
    finally:
        r.close()

    times = []
    for item in data.get("data", []):
        attr = item.get("attributes", {})
        t = attr.get("departure_time") or attr.get("arrival_time")
        if t:
            times.append(t)

    return times[:2]  # next 2

# ------------ DISPLAY SCREEN ------------
def show(bus1, bus2, blue1, blue2):
    lcd.clear()

    # Row 1 header
    mv(0, 0)
    lcd.putstr("116 ")
    lcd.putchar(chr(0))      # speaker_icon icon

    mv(10, 0)
    lcd.putstr("Blue ")
    lcd.putchar(chr(1))      # bell_icon icon

    # Row 2 (next)
    mv(0, 1)
    put("--" if bus1  is None else ("Arriving" if bus1  <= 0 else f"{bus1} min"))

    mv(10, 1)
    put("--" if blue1 is None else ("Arriving" if blue1 <= 0 else f"{blue1} min"))

    # Row 3 (then)
    mv(0, 2)
    put("--" if bus2  is None else ("Arriving" if bus2  <= 0 else f"{bus2} min"))

    mv(10, 2)
    put("--" if blue2 is None else ("Arriving" if blue2 <= 0 else f"{blue2} min"))

    # Row 4 timestamp
    t = time.localtime()
    mv(0, 3)
    put(f"Updated: {t[3]:02d}:{t[4]:02d}:{t[5]:02d}")

# ------------ WIFI CONNECT ------------
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PW)
        while not wlan.isconnected():
            time.sleep(0.2)
    return wlan.ifconfig()[0]

# ------------ MAIN LOOP ------------
def main():
    ip = connect_wifi()
    lcd.clear()
    mv(0,0); put("WiFi Connected")
    mv(0,1); put(ip)
    time.sleep(1)

    night_cleared = False  # to avoid flickering clear every loop at night

    while True:
        if in_night_mode():
            # Night mode: turn off backlight and stop hitting API
            if not night_cleared:
                lcd.clear()
                lcd.hal_backlight_off()
                night_cleared = True
            # check time roughly every minute
            time.sleep(60)
            continue
        else:
            # Daytime: ensure backlight is on
            lcd.hal_backlight_on()
            night_cleared = False

        try:
            # BUS inbound
            bus_preds = fetch_predictions(BUS_ROUTE_ID, BUS_STOP_ID, BUS_DIR_ID)
            bus1 = minutes_until(bus_preds[0]) if len(bus_preds) >= 1 else None
            bus2 = minutes_until(bus_preds[1]) if len(bus_preds) >= 2 else None

            # BLUE inbound
            blue_preds = fetch_predictions(BLUE_ROUTE_ID, BLUE_STOP_ID, BLUE_DIR_ID)
            blue1 = minutes_until(blue_preds[0]) if len(blue_preds) >= 1 else None
            blue2 = minutes_until(blue_preds[1]) if len(blue_preds) >= 2 else None

            show(bus1, bus2, blue1, blue2)

        except Exception as e:
            lcd.clear()
            mv(0,0); put("API Error")
            mv(0,1); put(str(e)[:18])

        time.sleep(5)

main()


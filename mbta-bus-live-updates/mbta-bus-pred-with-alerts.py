# DOESNT ACCOUNT FOR DST; ASSUMES BOSTON IS UTC-5 ALWAYS

import network, time, json
from machine import I2C, Pin
from machine_i2c_lcd import I2cLcd   # IMPORTANT: Using your driver!
import ntptime

try:
    import urequests as requests
except:
    import requests


def sync_time():
    try:
        ntptime.settime()   # sets board time to UTC
    except Exception as e:
        # If it fails, we just skip; RTC will look bogus
        pass


# ------------ WIFI ------------
WIFI_SSID = ""
WIFI_PW   = ""

# ------------ MBTA CONFIG ------------
BUS_ROUTE_ID    = "116"
BUS_STOP_ID     = "5733"
BUS_DIR_ID      = "1"     # inbound

BLUE_ROUTE_ID   = "Blue"
BLUE_STOP_ID    = "place-aport"
BLUE_DIR_ID     = "0"     # inbound for blue line
BUS_MINS_THRESHOLD = 3

API_KEY = ""

# ------------ LCD SETUP (I2C1 GP26/GP27) ------------
i2c = I2C(1, sda=Pin(26), scl=Pin(27), freq=100_000)
addr = (i2c.scan() or [0x27])[0]
lcd = I2cLcd(i2c, addr, 4, 20)

# ------------ BUTTON + BUZZER PINS ------------
BUTTON_PIN = 15  # button: one leg to GP15, other leg to GND, use PULL_UP
BUZZER_PIN = 14  # active buzzer

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
buzzer = Pin(BUZZER_PIN, Pin.OUT)
buzzer.value(0)  # buzzer off

# ------------ CUSTOM ICONS ------------

# Bell (for BUS)
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

# speaker (for BLUE LINE)
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

lcd.custom_char(0, speaker_icon)
lcd.custom_char(1, bell_icon)

# ------------ HELPERS ------------
def mv(c, r):
    lcd.move_to(c, r)

def put(s):
    lcd.putstr(s)

TZ_OFFSET_SECONDS = -5 * 3600   # Boston ≈ UTC-5 (ignoring DST)

def has_valid_time():
    return time.localtime()[0] >= 2024

def local_hour():
    now_utc = time.time()
    now_local = now_utc + TZ_OFFSET_SECONDS
    return time.localtime(now_local)[3]

def in_night_mode():
    if not has_valid_time():
        return False
    h = local_hour()
    return (h >= 23) or (h < 6)

def minutes_until(iso_str):
    try:
        # Example: '2025-11-13T22:10:00-05:00'
        date, clock = iso_str.split("T")
        y, m, d = map(int, date.split("-"))

        # Strip timezone offset part (-05:00 or +00:00)
        clock = clock.split("-")[0].split("+")[0]
        hh, mm, ss = map(int, clock.split(":"))

        # Target is in LOCAL time
        target_local = time.mktime((y, m, d, hh, mm, ss, 0, 0))

        now_tuple = time.localtime()
        if now_tuple[0] < 2024:
            return None  # RTC not valid yet → show "--"

        now_utc = time.time()
        now_local = now_utc + TZ_OFFSET_SECONDS

        return int((target_local - now_local) / 60)

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

# ------------ BUZZER HELPER ------------
def beep(times=3, on_ms=200, off_ms=150):
    for _ in range(times):
        buzzer.value(1)
        time.sleep_ms(on_ms)
        buzzer.value(0)
        time.sleep_ms(off_ms)

# ------------ STATUS LINE (ROW 4) ------------
def update_status_line(alert_armed):
    mv(0, 3)
    if alert_armed:
        put("Next bus alert ON")
    else:
        now_utc = time.time()
        now_local = now_utc + TZ_OFFSET_SECONDS
        lt = time.localtime(now_local)
        put(f"Updated: {lt[3]:02d}:{lt[4]:02d}:{lt[5]:02d}  ")

# ------------ DISPLAY SCREEN ------------
def show(bus1, bus2, blue1, blue2, alert_armed):
    lcd.clear()

    # Row 1 header
    mv(0, 0)
    lcd.putstr("116 ")
    lcd.putchar(chr(0))      # speaker icon

    mv(10, 0)
    lcd.putstr("Blue ")
    lcd.putchar(chr(1))      # bell icon

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

    # Row 4: status line
    update_status_line(alert_armed)

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
    sync_time()

    night_cleared = False

    alert_armed = False
    prev_button = button.value()   # start from actual state (1 = released)

    while True:
        # --- NIGHT MODE HANDLING ---
        if in_night_mode():
            if not night_cleared:
                lcd.clear()
                lcd.hal_backlight_off()
                night_cleared = True
            time.sleep(60)
            continue
        else:
            if night_cleared:
                lcd.hal_backlight_on()
                night_cleared = False

        # --- 1) FETCH + DISPLAY PREDICTIONS ONCE ---
        try:
            # BUS inbound (116)
            bus_preds = fetch_predictions(BUS_ROUTE_ID, BUS_STOP_ID, BUS_DIR_ID)
            bus1 = minutes_until(bus_preds[0]) if len(bus_preds) >= 1 else None
            bus2 = minutes_until(bus_preds[1]) if len(bus_preds) >= 2 else None

            # BLUE inbound
            blue_preds = fetch_predictions(BLUE_ROUTE_ID, BLUE_STOP_ID, BLUE_DIR_ID)
            blue1 = minutes_until(blue_preds[0]) if len(blue_preds) >= 1 else None
            blue2 = minutes_until(blue_preds[1]) if len(blue_preds) >= 2 else None

            show(bus1, bus2, blue1, blue2, alert_armed)

        except Exception as e:
            lcd.clear()
            mv(0,0); put("API Error")
            mv(0,1); put(str(e)[:18])
            bus1 = None  # avoid using stale value below

        # --- 2) FOR ABOUT 5 SECONDS, POLL BUTTON FREQUENTLY ---
        for _ in range(50):  # 50 * 0.1s = ~5 seconds
            curr_button = button.value()

            # FALLING EDGE (1 -> 0) = button pressed (because of PULL_UP + GND)
            if (prev_button == 1) and (curr_button == 0):
                print("button")
                alert_armed = not alert_armed
                if alert_armed:
                    # tiny confirmation beep when arming
                    beep(1, on_ms=80, off_ms=0)
                update_status_line(alert_armed)

            prev_button = curr_button

            # --- 3-MINUTE ALERT LOGIC (for 116 next bus) ---
            if alert_armed and (bus1 is not None):
                if 0 <= bus1 <= BUS_MINS_THRESHOLD:
                    beep(times=5)
                    alert_armed = False
                    update_status_line(alert_armed)

            time.sleep(0.1)

# run
main()


# 🚌 MBTA Arrival Display  
### Raspberry Pi Pico W • 20×4 I²C LCD • Button Alert • Active Buzzer

A compact IoT project that displays **real-time MBTA arrival predictions** for the **116 bus** and the **Blue Line**, using MicroPython on a **Raspberry Pi Pico W**.  
A tactile button lets you arm an alert — when the next 116 bus is within **3 minutes**, a buzzer sounds and the alert resets automatically.

Ideal as a small desktop/wall display for commuters.

Watch the Demo here
[![Watch the demo](https://img.youtube.com/vi/6VLtv4k-_vk/maxresdefault.jpg)](https://www.youtube.com/watch?v=6VLtv4k-_vk)

---

## ✨ Features

- **Live MBTA data** (v3 API)
- Displays:
  - Next + following **116 bus** arrival
  - Next + following **Blue Line** arrival
  - Last update timestamp
- **Alert mode** (toggled by button)
  - LCD shows: `Next bus alert ON`
  - When bus ≤ 3 minutes → buzzer beeps ×5
  - Alert automatically turns off
- **Night Mode (23:00–06:00)**
  - LCD backlight off  
  - No API polling
- Fast, responsive button handling  
- Clean, readable 20×4 layout  
- Fully customizable threshold, routes, pins

---

## 🧰 Hardware Required

| Component | Description |
|----------|-------------|
| **Raspberry Pi Pico W** | Wi-Fi microcontroller running MicroPython |
| **20×4 I²C LCD (PCF8574 backpack)** | Display module for predictions |
| **Active buzzer** | Simple high/low beep output |
| **Tactile pushbutton (4-leg)** | Arms/disarms bus alert |
| **Breadboard + jumpers** | For wiring |
| **USB cable / 5V power** | To power the Pico W |

---
## Setup Images

<p align="center">
  <img src="https://github.com/user-attachments/assets/1bee2197-c70d-4bd8-a355-78eecb252403" width="45%">
  <img src="https://github.com/user-attachments/assets/d2293007-f61f-4582-816b-fb2b2fa33fcd" width="45%">
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/48ef297c-1630-44cf-8689-9b4eabf1e8c7" width="45%">
  <img src="https://github.com/user-attachments/assets/04472e3d-b8b6-463e-8b6f-524b06023b74" width="45%">
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/839d0c3d-5df5-436f-821d-382bbaede44f" width="45%">
</p>


---

## 🔌 Wiring

### LCD → Pico W

| LCD Pin | Pico Pin |
|---------|----------|
| VCC     | 5V or 3V3 |
| GND     | GND |
| SDA     | GP26 |
| SCL     | GP27 |

### Button (Active-Low, using PULL_UP)

| Button Pin | Pico Pin |
|------------|----------|
| Leg 1      | GP15 |
| Opposite leg | GND |

### Buzzer

| Buzzer Pin | Pico Pin |
|------------|-----------|
| +          | GP14 |
| –          | GND |

---

## 📦 Software Setup

### 1. Flash MicroPython  
Install the latest MicroPython firmware for the Pico W.

### 2. Upload files to the Pico  
Required Python files:

main.py
machine_i2c_lcd.py
urequests.py (if not built-in)


Use **Thonny** to upload to the Pico’s filesystem.

### 3. Update configuration inside `main.py`

Set your Wi-Fi & MBTA API key:

```python
WIFI_SSID = "your-wifi"
WIFI_PW   = "your-password"
API_KEY   = "your-mbta-api-key"
```
## ▶️ Usage

### **Normal Mode**
On startup, the display shows:
- 116 next arrival
- 116 following arrival
- Blue Line next + following arrivals
- Updated timestamp on the bottom row

---

### **Arm Alert**
Press the button once:
- Bottom line updates to: `Next bus alert ON`
- When the next 116 bus is ≤ threshold (default **3 min**):
  - Buzzer beeps ×5  
  - Alert automatically resets  
  - Bottom line returns to timestamp

---

### **Disarm Alert**
Press the button again to turn the alert off.

---

### **Night Mode**
Active between **23:00–06:00**:
- LCD backlight turns off
- No MBTA API polling
- Automatically resumes normal operation after 06:00

---

## 🧠 How It Works (Internal Logic)

- Button uses **falling-edge detection** (PULL_UP → pressed = `0`)
- Button is scanned every **0.1 seconds** for fast responsiveness
- Predictions refresh every **~5 seconds**
- LCD is redrawn on every update cycle
- Alert state persists during the 5-second prediction cycle
- Night mode reduces network usage and turns off LCD light

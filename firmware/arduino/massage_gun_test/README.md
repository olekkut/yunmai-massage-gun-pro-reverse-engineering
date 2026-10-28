# 25 kHz Ultrasonic PWM Motor Test Harness

This directory contains the firmware test harness for bench-testing and diagnosing the **Dongguan E-S Motor 2430BL** series 3-phase brushless DC motor utilized in the **Yunmai Massage Gun Pro (Model YMFG-B563)**.

The test rig targets an **Arduino Nano** or **Arduino Uno** (Microchip ATmega328P running at 16 MHz) and generates a hardware-timed **25 kHz Fast PWM** control signal on Pin D9, completely bypassing a faulty motherboard to verify whether the motor and its integrated driver are functional.

---

## Table of Contents
1. [Why Default Arduino analogWrite() Fails](#why-default-arduino-analogwrite-fails)
2. [Hardware Timer1 25 kHz Configuration](#hardware-timer1-25-khz-configuration)
3. [Wiring Schematic](#wiring-schematic)
4. [Active-LOW Logic & Speed Mapping](#active-low-logic--speed-mapping)
5. [Serial CLI Commands](#serial-cli-commands)
6. [Compiling & Uploading](#compiling--uploading)
7. [Bench Testing & Safety Procedure](#bench-testing--safety-procedure)

---

## Why Default Arduino analogWrite() Fails

Standard Arduino boards provide default PWM via the `analogWrite()` function. However:
- Pins 3, 9, 10, and 11 operate at **490 Hz**.
- Pins 5 and 6 operate at **980 Hz**.

The Dongguan E-S Motor 2430BL integrated motor driver specification mandates a PWM input frequency between **15 kHz and 25 kHz** (maximum 60 kHz):
1. **Acoustic Noise**: At 490 Hz or 980 Hz, the stator coils resonate mechanically within the human audio band, emitting a loud, high-pitched screeching tone.
2. **Torque Pulsation & Driver Lockout**: Low-frequency ripple overwhelms the internal RC input filter and gate drive logic of the built-in 3-phase inverter ASIC, causing erratic rotor vibration, high current spikes, or immediate driver protection lockout.
3. **Ultrasonic Silence**: Driving at 25 kHz places the electrical switching ripple well above the human hearing limit (20 kHz), allowing whisper-quiet and smooth torque delivery across all speed ranges.

---

## Hardware Timer1 25 kHz Configuration

To achieve exactly 25 kHz without CPU jitter, the sketch directly configures the 16-bit ATmega328P **Timer1** in **Fast PWM Mode 14** with `ICR1` (Input Capture Register 1) defining the `TOP` counter value.

### Frequency Calculation Formula
$$f_{\text{PWM}} = \frac{f_{\text{CPU}}}{N \times (1 + \text{ICR1})}$$

Where:
- $f_{\text{CPU}} = 16\,000\,000\,\text{Hz}$ (16 MHz system clock)
- $N = 1$ (Prescaler = 1, no clock division)
- $f_{\text{PWM}} = 25\,000\,\text{Hz}$ (Target frequency = 25 kHz)

Solving for `ICR1`:
$$\text{ICR1} = \frac{16\,000\,000}{1 \times 25\,000} - 1 = 640 - 1 = 639$$

### Register Configuration Code
```cpp
// Configure Timer1 for 25kHz Fast PWM on Pin 9 (OC1A)
TCCR1A = 0;
TCCR1B = 0;
TCNT1  = 0;

// COM1A1: Clear OC1A on Compare Match, set at BOTTOM (Non-inverting)
// WGM11: Fast PWM Mode 14 (part 1)
TCCR1A = (1 << COM1A1) | (1 << WGM11);

// WGM13, WGM12: Fast PWM Mode 14 (part 2, ICR1 = TOP)
// CS10: Clock select = Prescaler 1 (no prescaling)
TCCR1B = (1 << WGM13) | (1 << WGM12) | (1 << CS10);

ICR1  = 639; // TOP value yields 25,000 Hz
OCR1A = 0;   // Initialize with 0% duty cycle
```

With `ICR1 = 639`, the duty cycle has a resolution of 640 discrete steps ($0$ to $639$).

---

## Wiring Schematic

### Pin Connection Table

| Arduino Pin | Signal Name | Motor CN2 Pin | Motor Wire Color | Description |
|---|---|---|---|---|
| **D9 (OC1A)** | PWM Output | Pin 5 | **Blue** (or Purple) | 25 kHz Active-LOW speed control signal |
| **D8** | Direction (FR)| Pin 3 | **Yellow** | Rotation direction (LOW: CW, HIGH: CCW) |
| **D2 (INT0)** | Tachometer (FG)| Pin 2 | **White** | Speed feedback (6 pulses per mechanical revolution) |
| **GND** | Logic Ground | Pin 4 | **Black** | Common ground reference (**MUST connect to Battery GND**) |
| *None* | High Voltage | Pin 1 | **Red** | Connect directly to +21.6V to +26V Battery / PSU |

> ⚠️ **CRITICAL ELECTRICAL WARNING**:
> - **NEVER** connect the Red motor wire (21.6V-26V) to any Arduino pin or Arduino 5V rail! Doing so will instantly vaporize the microcontroller.
> - **ALWAYS** establish a common Ground between Arduino GND, Motor GND (Black wire), and the Battery/PSU Ground.

### ASCII Wiring Diagram

```text
               +---------------------------+
               | 21.6V - 26V Power Supply  |
               |     or Li-ion Pack        |
               +-------------+-------------+
                             |
                   +24V (Red)|    GND (Black)
                   +---------+--------+
                   |                  |
                   |                  +---------------------+
                   |                                        |
                   |                                        |
       +-----------v-----------+               +------------v------------+
       |   Dongguan 2430BL     |               |   Arduino Uno / Nano    |
       |     BLDC Motor        |               |      (ATmega328P)       |
       |  (Integrated Driver)  |               |                         |
       |                       |               |                         |
       |  Pin 1: Vm (Red)  <---+               |                         |
       |  Pin 2: FG (White)----+-------------> | D2 (INT0 / Tachometer)  |
       |  Pin 3: FR (Yellow)<----------------- | D8 (Direction Control)  |
       |  Pin 4: GND (Black)---+-------------> | GND (Common Ground)     |
       |  Pin 5: PWM (Blue)  <----------------- | D9 (OC1A / 25kHz PWM)   |
       +-----------------------+               +-------------------------+
                                                            |
                                                       USB to PC
                                                     (115200 Baud)
```

---

## Active-LOW Logic & Speed Mapping

The built-in driver in the Dongguan E-S Motor 2430BL operates using **active-LOW logic**:
- **High Level ($V_{IH} \ge 2.0\text{V}$ or Open / Floating)**: Driver turns **OFF** (Fail-safe idle state).
- **Low Level ($V_{IL} \le 0.5\text{V}$)**: Driver turns **ON** (Maximum speed).

The sketch handles this inversion via the `invertedLogic` boolean flag:

```cpp
void setMotorSpeed(int percent) {
  currentSpeed = percent;
  int duty = 0;
  
  if (invertedLogic) {
     // Active-LOW logic: 0% speed -> 5V (ICR1), 100% speed -> 0V (0)
     duty = map(percent, 0, 100, ICR1, 0);
  } else {
     // Standard active-HIGH logic: 0% speed -> 0V (0), 100% speed -> 5V (ICR1)
     duty = map(percent, 0, 100, 0, ICR1);
  }

  OCR1A = duty; // Update Timer1 Output Compare Register directly
}
```

When `invertedLogic = true`:
- Requesting `0%` sets `OCR1A = 639` (Constant HIGH $\approx 5\text{V}$), turning the motor OFF.
- Requesting `50%` sets `OCR1A = 319` (50% square wave), running the motor at half speed.
- Requesting `100%` sets `OCR1A = 0` (Constant LOW $\approx 0\text{V}$), running the motor at full speed.

---

## Serial CLI Commands

Connect to the Arduino using the Serial Monitor at **115200 baud** with **Newline** line ending.

| Command | Description | Example Input | Expected Output |
|---|---|---|---|
| `0` - `100` | Set motor speed percentage | `45` | `Speed: 45% (OCR1A: 287/639)` |
| `s` or `S` | Emergency Stop (0% duty) | `s` | `Speed: 0% (OCR1A: 0/639)` |
| `r` or `R` | Toggle Direction (Forward / Reverse) | `r` | `Direction: Reverse` |
| `i` or `I` | Toggle Inverted Active-LOW Logic Mode | `i` | `Logic Inverted: YES` |

---

## Compiling & Uploading

### Option A: Arduino IDE
1. Open `firmware/arduino/massage_gun_test/massage_gun_test.ino` in Arduino IDE.
2. Select **Tools > Board > Arduino AVR Boards > Arduino Nano** (or Arduino Uno).
3. If using an Arduino Nano clone (CH340 USB chip), select **Tools > Processor > ATmega328P (Old Bootloader)**.
4. Select the corresponding serial COM port under **Tools > Port**.
5. Click **Upload** (Ctrl + U).

### Option B: Arduino CLI
```powershell
# Compile sketch
arduino-cli compile --fqbn arduino:avr:nano firmware/arduino/massage_gun_test/massage_gun_test.ino

# Upload to connected board (e.g. COM3)
arduino-cli upload -p COM3 --fqbn arduino:avr:nano firmware/arduino/massage_gun_test/massage_gun_test.ino
```

---

## Bench Testing & Safety Procedure

1. **Mechanical Restraint**: The massage gun motor produces high rotational torque. Securely clamp the motor chassis to your workbench before applying power.
2. **Current-Limited Power Supply**: When testing for the first time, use a lab bench power supply set to **24.0V** with current limit set to **1.0A**. Normal idle motor draw is ~0.2A - 0.5A without mechanical percussion load.
3. **Verify Grounding**: Ensure Arduino GND is firmly connected to PSU Ground before applying 24V.
4. **Boot Sequence**:
   - Power on the Arduino first.
   - Open Serial Monitor at 115200 baud and confirm the prompt `Yunmai Motor HF Test Ready (25kHz)`.
   - Power on the 24V motor supply.
   - Enter `15` to command a gentle 15% spin test.
   - If motor does not spin, press `i` to toggle active-LOW logic mode.
   - Enter `s` to verify stopping behavior.

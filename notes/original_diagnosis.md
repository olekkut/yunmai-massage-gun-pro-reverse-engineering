# Diagnosis Log: Yunmai Massage Gun Pro

## Component Identification
- **Device Model**: Yunmai Massage Gun Pro (YMFG-B563)
- **Main Board**: `YM-B563-MAIN-V0.3` (Date: 2021-09-22)
  - **MCU**: U4 (TSSOP package, likely handling logic, UI, and PWM generation).
  - **Power Stage**: Inductor `470` and Capacitor `50V` near input suggests a Buck Converter for low-voltage logic (3.3V/5V).
  - **Motor Connector**: CN2 (5-pin, Top edge).
  - **UI/Battery Connector**: Unlabeled large connector (Bottom edge), pins match user notes explicitly.

## Pinout Analysis

### Motor Interface (CN2)
Confirmed by user notes and Image `3c057de5`. The motor has an **Integrated Driver**.

| Pin | Color  | Function | Voltage Level | Notes |
|-----|--------|----------|---------------|-------|
| 1   | Red    | **VCC**  | 26V (Battery) | Main Power |
| 2   | White  | **FG**   | 3.3V/5V Logic | Frequency Generator (Speed Feedback) |
| 3   | Yellow | **FR**   | Logic Level   | Direction (CW/CCW). Ground or VCC? |
| 4   | Black  | **GND**  | 0V            | Common Ground |
| 5   | Blue   | **PWM**  | Logic Level   | Speed Control (Duty Cycle) |

*Note*: Pin 1 is likely the Left-most pin when looking at the connector from the wire insertion side, but verify with the Red wire.

### UI/Power Connector (Bottom)
Matches board labels in Image `5cbf4b6f`.

| Pin Label | Wire Color | Function | Notes |
|-----------|------------|----------|-------|
| DC+       | Black (Thick)| Battery + | **26V Input** |
| DC-       | Black (Thick)| Battery - | Ground |
| 1         | Yellow (Thin)| LED Anode | Common + for LEDs |
| 2         | White      | LED Red   | Cathode |
| 3         | Blue       | LED White | Cathode |
| 4         | Green      | LED 1/3   | Cathode |
| 5         | Brown      | LED 2/3   | Cathode |
| 6         | Grey       | LED 3/3   | Cathode |
| 7         | Orange     | Button 2  | Tactile Switch |
| 8         | Violet     | Button 1  | Tactile Switch |
| KEY       | Black      | Switch    | Logic Signal |
| GND       | Red (Thin) | GND       | Logic Ground (Check color-label match!)|

**CRITICAL WARNING**: The board label `GND` corresponds to "Thin Red Wire" in user notes. This is a severe color-coding violation. **ALWAYS trust the Board Labels (screen printing) over wire colors.**

## Fault Hypotheses
1.  **Power Failure (Logic)**: The step-down converter on the board is dead, so the MCU doesn't wake up.
2.  **Motor Driver Failure**: The internal driver in the motor is dead.
3.  **Signal Path**: PWM signal is not being generated.
4.  **Battery Protection**: The battery BMS might be locked or outputting 0V.

## Proposed Test Plan
1.  **Check Input Power**: Measure Voltage at `DC+` / `DC-`. Should be ~26V.
2.  **Check Logic Power**: Find the regulator (near Inductor 470) and measure output (across capacitors C15 or C19?). Should be 3.3V or 5V.
3.  **Bypass Test (Motor)**:
    -   Disconnect Motor from Board.
    -   Apply 24V to Motor Red/Black.
    -   Connect Motor Blue (PWM) to Motor Red (VCC) through a 1k resistor (or direct if safe) to command 100% speed.
    -   *If motor spins, the motor is good.*

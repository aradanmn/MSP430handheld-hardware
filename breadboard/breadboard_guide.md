# MSP430G2553 Game Boy - Breadboard Assembly Guide

## Board Overview
- **Board Model:** Elenco 9440
- **Layout:** 4 panels (A, B, C, D) left-to-right
- **Each Panel:** 2 strips of 5 tie-points wide, ~60 rows deep
- **Power Rails:** VCC (red) + GND (black) at top, spanning all panels

---

## Component Placement Reference

| Component | Panel | Rows | Width | Notes |
|-----------|-------|------|-------|-------|
| **MSP430 LaunchPad** | B-C | 5-14 | Center gap | 10 pins each side (J1 left, J2 right) |
| **SN74HC165N (Shift Reg)** | A | 20-27 | Center gap | DIP-16, 8 button inputs |
| **LM386N-1 (Audio Amp)** | D | 20-23 | Center gap | DIP-8, PWM input → speaker output |
| **SP-3605 Speaker** | D | 28-30 | Tie points | Just header connections for leads |
| **DFR0650 OLED (I2C)** | A | 5-8 | Header pins | 4-pin SDA/SCL/VCC/GND |
| **Pot Volume (10K Log)** | D | 10-12 | Tie points | Wiper to LM386 pin 3 |
| **Pot ADC (10K Linear)** | A | 10-12 | Tie points | Wiper to LaunchPad P1.3 |
| **Resistors 10K (×8)** | B | 30-39 | Tie points | Button pull-ups for shift register |
| **Resistors 10K (×2)** | C | 30-31 | Spare | Backup/alternative placement |
| **Resistor 1K (×1)** | C | 35-36 | Tie points | RC filter P1.2 → LM386 |
| **Caps 0.1µF (×2)** | C | 37-40 | Tie points | RC filter + LM386 bypass |
| **Buttons B3F-1000 (×8)** | A + D | 35-50 | Columns | 4 per side, legs to shift reg + GND |
| **LiPo Charger (USB-C)** | D | 5-8 | Header pins | VCC out to VCC rail, GND to GND rail |

---

## Critical Wiring Connections

| From (Source) | To (Destination) | Wire Color | Purpose |
|---------------|------------------|-----------|---------|
| LaunchPad P2.4 | SN74HC165N Pin 1 (SH/LD) | Orange | Shift reg load (active LOW) |
| LaunchPad P1.5 (CLK) | SN74HC165N Pin 2 (CLK) | Yellow | SPI clock |
| SN74HC165N Pin 9 (QH) | LaunchPad P1.7 (SOMI) | Green | Serial button data |
| LaunchPad P1.2 (PWM) | 1K Ω resistor → LM386 Pin 3 | Red | Audio PWM signal |
| 0.1µF cap | P1.2 to GND | - | RC filter (audio) |
| LM386 Pin 5 | Speaker (+) | White | Amplified audio out |
| Speaker (-) | GND | Black | Audio return |
| LaunchPad P1.6 (SCL) | OLED SCL | Blue | I2C clock |
| LaunchPad P1.7 (SDA) | OLED SDA | Cyan | I2C data |
| LaunchPad P1.3 | ADC Pot Wiper | Brown | Analog input |
| Vol Pot (Wiper) | LM386 Pin 3 (parallel) | Purple | Volume control |
| All SR Pins 3-10 | Button legs + 10K pulls | Purple | Button matrix D0-D7 |
| LaunchPad VCC | VCC Rail (all panels) | Red | Main power |
| LaunchPad GND | GND Rail (all panels) | Black | Ground return |
| LM386 Pin 6 (VCC) | VCC Rail | Red | Power to amplifier |
| LM386 Pin 4 (GND) | GND Rail | Black | Ground to amplifier |
| SR Pin 16 (VCC) | VCC Rail | Red | Power to shift register |
| SR Pin 8 (GND) | GND Rail | Black | Ground to shift register |
| SR Pin 15 (CLK INH) | GND Rail | Black | Clock inhibit (tie LOW) |
| Charger VCC | VCC Rail | Red | Battery output to power rail |
| Charger GND | GND Rail | Black | Battery ground to power rail |

---

## Assembly Order (Step-by-Step)

### Phase 1: Power Infrastructure
1. **Install power rails** on top of breadboard (red VCC, black GND)
2. **Connect VCC wire** from LaunchPad pin 1 or 10 to red power rail
3. **Connect GND wire** from LaunchPad pin 20 to black power rail
4. **Test power** with multimeter: should read ~3.3V between rails

### Phase 2: Main ICs
5. **Insert MSP430 LaunchPad** into Panel B-C (rows 5-14, center gap)
   - J1 left header into Panel B
   - J2 right header into Panel C
   - Verify orientation and row alignment
6. **Insert SN74HC165N** shift register into Panel A (rows 20-27, center gap)
   - Pin 1 facing left (away from panels)
   - Pin 16 (VCC) to power, Pin 8 (GND) to ground
7. **Insert LM386N-1** audio amp into Panel D (rows 20-23)
   - Pin 6 to VCC, Pin 4 to GND
   - Pin 15 to GND (clock inhibit)

### Phase 3: Support Components
8. **Install 10K Ω pull-up resistors** (8×) in Panel B rows 30-39
   - One lead to VCC rail, other to shift register input lines (Pins 3-10)
9. **Install 1K Ω resistor** Panel C rows 35-36
   - From LaunchPad P1.2 to LM386 pin 3 input
10. **Install 0.1µF capacitors** (2×) Panel C rows 37-40
    - Cap 1: P1.2 to GND (RC filter)
    - Cap 2: VCC to GND near LM386 (bypass)

### Phase 4: Control & I/O Modules
11. **Install DFR0650 OLED** header into Panel A rows 5-8
    - VCC to rail, GND to rail, SCL to P1.6, SDA to P1.7
12. **Install potentiometers** (tied to power via tie-points)
    - Volume pot (10K log) Panel D rows 10-12 (wiper parallel to LM386 pin 3)
    - ADC pot (10K linear) Panel A rows 10-12 (wiper to P1.3)
13. **Install Adafruit 4410 LiPo Charger** Panel D rows 5-8
    - VCC out to red rail, GND to black rail, BAT+/BAT- isolated for now

### Phase 5: Buttons & Final Wiring
14. **Insert buttons (8×)** into Panel A & D rows 35-50
    - 4 buttons per panel (2 columns of 2)
    - One leg to shift register input (via pull-up), other leg to GND
15. **Connect critical signal wires:**
    - P2.4 → SR Pin 1 (SH/LD)
    - P1.5 → SR Pin 2 (CLK)
    - SR Pin 9 (QH) → P1.7 (SOMI)
    - SR Pins 3-10 → Button matrix (with 10K pulls to VCC)

### Phase 6: Power & Audio
16. **Verify all power connections** are complete
17. **Connect speaker** leads to Panel D rows 28-30
    - Speaker (+) to LM386 pin 5 output
    - Speaker (-) to GND
18. **Final visual inspection** for shorts, reversed ICs, missing connections

---

## Pinout Reference

### MSP430G2553 LaunchPad Headers

**J1 (Left, rows 5-14):**
- Pin 1: VCC
- Pin 2: P1.0
- Pin 3: P1.1
- Pin 4: P1.2 (PWM audio output)
- Pin 5: P1.3 (ADC for pot)
- Pin 6: P1.4
- Pin 7: P1.5 (UCB0CLK / SPI clock)
- Pin 8: RST
- Pin 9: TEST
- Pin 10: GND

**J2 (Right, rows 5-14):**
- Pin 1: GND
- Pin 2: P1.6 (UCB0SCL / I2C clock)
- Pin 3: P1.7 (UCB0SDA/SOMI / I2C data)
- Pin 4: P2.0
- Pin 5: P2.1
- Pin 6: P2.2
- Pin 7: P2.3
- Pin 8: P2.4 (Shift reg load control)
- Pin 9: P2.5
- Pin 10: VCC

### SN74HC165N Shift Register (DIP-16)
- Pin 1: SH/LD (load control) ← P2.4
- Pin 2: CLK (shift clock) ← P1.5
- Pin 3-10: D0-D7 (parallel inputs) ← Button matrix
- Pin 9: QH (serial output) → P1.7
- Pin 15: CLK INH (clock inhibit) → GND
- Pin 16: VCC
- Pin 8: GND

### LM386N-1 Audio Amplifier (DIP-8)
- Pin 1: Gain control (to GND for 20dB gain)
- Pin 2: ±IN (inverting input) → GND
- Pin 3: +IN (non-inverting) ← P1.2 (via 1K + 0.1µF filter)
- Pin 4: GND
- Pin 5: Output (to speaker+)
- Pin 6: VCC
- Pin 7: Bypass (0.1µF to GND)
- Pin 8: GND

---

## Testing Checklist

- [ ] Power rails measure 3.3V (LaunchPad) / 0V GND
- [ ] LaunchPad programs via USB without errors
- [ ] Shift register responds to button presses (GPIO toggle on P2.4)
- [ ] Serial data from SR Pin 9 appears on P1.7 (oscilloscope or logic analyzer)
- [ ] OLED display initializes and shows text (I2C communication)
- [ ] Audio amp produces sound when P1.2 outputs PWM tone
- [ ] Volume pot changes amplitude in real-time
- [ ] ADC pot changes analog value (verify via ADC read)
- [ ] All 8 buttons debounce cleanly in firmware
- [ ] No unexpected power draws (check for shorts)

---

## Troubleshooting Tips

| Issue | Likely Cause | Solution |
|-------|-------------|----------|
| LaunchPad won't program | USB connection loose or IC reversed | Check USB cable, verify pin orientation |
| Buttons not registering | Shift register pins 3-10 not connected | Verify button matrix wiring to SR parallel inputs |
| Audio distortion | Volume pot setting too high | Adjust wiper position on 10K log pot |
| OLED shows garbage | I2C clock/data reversed or no pull-ups | Check P1.6/P1.7 connections; OLED may need onboard pull-ups |
| Shift register not shifting | CLK inhibit (pin 15) not tied to GND | Connect pin 15 directly to GND |
| Power rail shows 0V | GND not connected from LaunchPad | Add GND wire from LaunchPad pin 20 to black rail |

---

## Notes

- **I2C/SPI Conflict:** P1.7 is used for both OLED SDA and SR SOMI. If you need concurrent I2C and SPI, implement software I2C for OLED, leaving hardware SPI for shift register.
- **Pull-up Strategy:** The 8 resistors in Panel B (rows 30-39) keep button inputs HIGH when not pressed. When button is pressed, it pulls the corresponding SR input LOW.
- **Audio Filtering:** The 1K + 0.1µF RC filter on P1.2 smooths PWM noise before the amplifier input. Critical for clean audio.
- **Pot Wiper Loading:** Both potentiometers have high impedance wipers; firmware should use software averaging/filtering to reduce jitter.
- **USB Power:** The Adafruit 4410 charger provides 3.3V output to power the breadboard. Remove LaunchPad USB cable once battery is connected to avoid backfeeding.

---

Generated: 2026-02-28

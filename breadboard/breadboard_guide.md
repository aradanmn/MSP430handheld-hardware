# MSP430G2553 Handheld — Breadboard Assembly Guide
_Revision: B — 2026-03-21_

## Board Overview

- **Board Model:** Elenco 9440 (4-panel full-size, 830 tie-points)
- **Panels:** A (leftmost) → B → C → D (rightmost), ~60 rows each
- **Center gap:** splits each panel into left and right 5-column halves
- **Power rails:** VCC (+, red) and GND (−, black) at top and bottom, spanning all panels

---

## Component Placement

| Component | Panel | Rows | Notes |
|-----------|-------|------|-------|
| **MSP430 LaunchPad** | B–C | 20–40 | Straddles center gap; J1 left into Panel B, J2 right into Panel C |
| **23LC1024-I/P (SRAM)** | A | 5–9 | DIP-8, straddles center gap |
| **W25Q128JVSSIQ (Flash)** | A | 12–16 | DIP-8 breakout (Adafruit #5634), straddles center gap |
| **SSD1325 OLED** | D | 5–12 | 2.7" SPI module; 7-pin header — see wiring below |
| **SN74HC165N (Shift Reg)** | A–B | 43–51 | DIP-16, straddles center gap |
| **LM386N-1 (Audio Amp)** | C–D | 43–48 | DIP-8, straddles center gap |
| **Vol Pot (10kΩ log)** | D | 52–54 | Wiper → LM386 pin 3 |
| **Speaker** | D | 56–58 | Header connection for leads |
| **Resistors 10kΩ (×8)** | B | 54–62 | Button pull-ups, one per button input |
| **Resistor 1kΩ (×1)** | C | 53–54 | PWM RC filter |
| **Capacitor 10µF (×1)** | C | 56–57 | RC filter output coupling |
| **Capacitor 0.1µF (×4)** | near ICs | — | Bypass: SRAM VCC, Flash VCC, SR VCC, spare |
| **Capacitors 10µF (×2)** | near LM386 | — | One on LM386 pin 7 (bypass), one input coupling |
| **Capacitor 220µF (×1)** | near LM386 | — | LM386 pin 5 output coupling |
| **Buttons B3F-1000 (×8)** | A + D | 54–62 | 4 per side; one leg to pull-up/SR input, other to GND |
| **LiPo Charger (Adafruit #4410)** | B–C | 5–8 | Header pins; VCC out → VCC rail, GND → GND rail |

---

## SPI Bus — Pin Assignments

All SPI devices share USCI_B0 (P1.5/P1.6/P1.7). CS pins are the only differentiators.

| Signal | MSP430 Pin | J Header | Direction | Connected to |
|--------|-----------|----------|-----------|-------------|
| SCLK | P1.5 | J1 pin 7 | Out | All SPI devices |
| MISO | P1.6 | J2 pin 2 | In | SRAM SO, Flash DO, SR QH |
| MOSI | P1.7 | J2 pin 3 | Out | OLED DI, SRAM SI, Flash DI |
| OLED CS | P2.0 | J2 pin 4 | Out (active LOW) | SSD1325 CS |
| OLED DC | P2.1 | J2 pin 5 | Out | SSD1325 D/C |
| OLED RST | P2.2 | J2 pin 6 | Out | SSD1325 RST |
| SRAM CS | P2.3 | J2 pin 7 | Out (active LOW) | 23LC1024 CS# |
| Flash CS | P2.4 | J2 pin 8 | Out (active LOW) | W25Q128 CS# |
| SR SH/LD | P2.5 | J2 pin 9 | Out (active LOW) | SN74HC165N pin 1 |

> **Note:** P1.6 is also LED2 on the LaunchPad. Remove the LED2 solder jumper (or leave it — it weakly pulls P1.6, which is tolerable for SPI MISO but can be trimmed for reliability).

---

## Critical Wiring Connections

### Power
| From | To | Wire | Purpose |
|------|----|------|---------|
| LaunchPad J1 pin 1 (VCC) | Top red rail | Red | System 3.3V |
| LaunchPad J1 pin 10 (GND) | Top black rail | Black | System GND |
| LaunchPad J2 pin 1 (GND) | Top black rail | Black | GND (other side) |

### SSD1325 OLED (SPI, 7-pin header)
| OLED Pin | MSP430 | Wire | Notes |
|----------|--------|------|-------|
| GND | GND rail | Black | |
| VCC | VCC rail | Red | 3.3V only |
| SCLK (D0) | P1.5 (J1 pin 7) | Yellow | Shared SPI clock |
| MOSI (D1) | P1.7 (J2 pin 3) | Blue | Shared MOSI |
| RST | P2.2 (J2 pin 6) | White | Toggle LOW on init |
| D/C | P2.1 (J2 pin 5) | Green | LOW=command, HIGH=data |
| CS | P2.0 (J2 pin 4) | Orange | Active LOW |

### 23LC1024-I/P SRAM (DIP-8)
| SRAM Pin | Signal | MSP430 | Wire |
|----------|--------|--------|------|
| 1: CS# | SRAM_CS | P2.3 (J2 pin 7) | Orange |
| 2: SO | MISO | P1.6 (J2 pin 2) | Green |
| 3: NC | — | — | Leave floating |
| 4: VSS | GND rail | — | Black |
| 5: SI | MOSI | P1.7 (J2 pin 3) | Blue |
| 6: SCK | SCLK | P1.5 (J1 pin 7) | Yellow |
| 7: HOLD# | VCC rail | — | Tie HIGH |
| 8: VCC | VCC rail | — | Red + 0.1µF bypass to GND |

### W25Q128JVSSIQ Flash (Adafruit #5634 DIP breakout)
| Flash Pin | Signal | MSP430 | Wire |
|-----------|--------|--------|------|
| 1: CS# | Flash_CS | P2.4 (J2 pin 8) | Orange |
| 2: DO | MISO | P1.6 (J2 pin 2) | Green |
| 3: WP# | VCC rail | — | Tie HIGH |
| 4: GND | GND rail | — | Black |
| 5: VCC | VCC rail | — | Red + 0.1µF bypass to GND |
| 6: HOLD# | VCC rail | — | Tie HIGH |
| 7: CLK | SCLK | P1.5 (J1 pin 7) | Yellow |
| 8: DI | MOSI | P1.7 (J2 pin 3) | Blue |

### SN74HC165N Shift Register (DIP-16, button input latch)
| SR Pin | Signal | Connection |
|--------|--------|-----------|
| 1: SH/LD# | SR_SH/LD | P2.5 (J2 pin 9) — LOW latches buttons |
| 2: CLK | SCLK | P1.5 (J1 pin 7) |
| 3–6: E,F,G,H | BTN5–8 | One button each; other button leg → GND |
| 7: QH# | — | Leave unconnected (inverted output, not used) |
| 8: GND | GND rail | Black |
| 9: QH | MISO | P1.6 (J2 pin 2) — serial button data out |
| 10: SER | GND | Tie LOW (no cascading) |
| 11–14: A,B,C,D | BTN1–4 | One button each; other button leg → GND |
| 15: CLK INH | GND | Tie LOW (always enabled) |
| 16: VCC | VCC rail | Red + 0.1µF bypass to GND |

### Audio (LM386N-1)
| Connection | Details |
|-----------|---------|
| P1.2 → 1kΩ → 10µF cap → pot wiper | RC filter: PWM → LM386 input path |
| Pot pin 1 (CW) | VCC rail |
| Pot pin 3 (CCW) | GND rail |
| Pot wiper → LM386 pin 3 (+IN) | Volume control |
| LM386 pin 2 (−IN) | GND |
| LM386 pin 4 (GND) | GND rail |
| LM386 pin 6 (VCC) | VCC rail |
| LM386 pin 7 (BYP) | 10µF to GND (noise bypass) |
| LM386 pin 5 (OUT) → 220µF → 10Ω → SPK+ | Output coupling + protection |
| Speaker − | GND |
| LM386 pins 1 & 8 | Leave open (20× gain default) |

### Button Pull-ups (×8)
Each button: one leg → 10kΩ → VCC rail; other leg → GND.
The 10kΩ junction also connects to the corresponding SR input pin (A–H).
Logic: idle = HIGH (VCC via pull-up); pressed = LOW (GND via button).

---

## LaunchPad Header Pinout (for reference)

**J1 (left header, 10 pins, Panel B):**

| J1 Pin | Signal | Notes |
|--------|--------|-------|
| 1 | VCC (3.3V) | Main power rail supply |
| 2 | P1.0 | LED1 (red) |
| 3 | P1.1 | RXD (UART) |
| 4 | P1.2 | PWM audio output (Timer_A TA0.1) |
| 5 | P1.3 | Button S2 (on-board) |
| 6 | P1.4 | Spare |
| 7 | P1.5 | SCLK (UCB0CLK) |
| 8 | RST | Active LOW reset |
| 9 | TEST | Leave unconnected |
| 10 | GND | |

**J2 (right header, 10 pins, Panel C):**

| J2 Pin | Signal | Notes |
|--------|--------|-------|
| 1 | GND | |
| 2 | P1.6 | MISO (UCB0SOMI) — also LED2 |
| 3 | P1.7 | MOSI (UCB0SIMO) |
| 4 | P2.0 | OLED CS (active LOW) |
| 5 | P2.1 | OLED D/C |
| 6 | P2.2 | OLED RST |
| 7 | P2.3 | SRAM CS (active LOW) |
| 8 | P2.4 | Flash CS (active LOW) |
| 9 | P2.5 | SR SH/LD# (active LOW latch) |
| 10 | VCC | |

---

## Assembly Phases

### Phase 1 — LaunchPad only (Lessons 01–05)
1. Insert LaunchPad into Panels B–C, rows 20–40 (J1 left, J2 right)
2. Connect J1 pin 1 (VCC) → top red rail
3. Connect J1 pin 10 (GND) → top black rail
4. Connect J2 pin 1 (GND) → top black rail
5. Plug in USB — LED1 should light

### Phase 2 — Display + Memory (Lessons 06–10)
6. Insert 23LC1024-I/P into Panel A, rows 5–9; wire per table above
7. Insert W25Q128 DIP breakout into Panel A, rows 12–16; wire per table above
8. Add 0.1µF bypass caps on SRAM VCC and Flash VCC pins
9. Place SSD1325 OLED module header in Panel D rows 5–12; wire per table above

### Phase 3 — Input (Lessons 11–13)
10. Insert SN74HC165N into Panels A–B, rows 43–51
11. Install 8 × B3F-1000 buttons and 8 × 10kΩ pull-ups
12. Wire buttons to SR inputs (A–H), SR to MCU SPI

### Phase 4 — Audio (Lessons 14–15)
13. Insert LM386N-1 into Panels C–D, rows 43–48
14. Wire RC filter (P1.2 → 1kΩ → 10µF → pot → LM386 pin 3)
15. Wire output (LM386 pin 5 → 220µF → 10Ω → speaker)
16. Add bypass caps on LM386 pin 7

### Phase 5 — Power (Lesson 16+)
17. Install Adafruit #4410 LiPo charger in Panels B–C, rows 5–8
18. Wire charger 3.3V out → VCC rail, GND → GND rail
19. Connect LiPo battery — remove LaunchPad USB cable

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| OLED shows nothing | SPI pins mis-wired or CS/DC swapped | Verify P2.0=CS, P2.1=DC, P2.2=RST |
| SRAM reads garbage | CS held LOW or floating | Confirm P2.3 → SRAM pin 1; HOLD# tied HIGH |
| Flash not responding | WP# or HOLD# floating LOW | Tie both to VCC |
| Buttons all read HIGH | SR SH/LD never pulsed | Confirm P2.5 (not P2.4) → SR pin 1 |
| Buttons all read LOW | CLK INH not grounded | Tie SR pin 15 → GND |
| No audio | RC filter reversed | P1.2 → 1kΩ → 10µF → pot → LM386 pin 3 |
| Audio distorted | Vol pot too high | Turn wiper toward GND end |
| P1.6/MISO always HIGH | LED2 jumper fighting MISO | Remove LED2 jumper on LaunchPad |

---

## SPI Tip — CS Management

Only one CS may be LOW at a time. When reading/writing any device, assert its CS LOW and keep all others HIGH. At startup, assert all CS pins HIGH in firmware before enabling USCI_B0.

---

_Updated: 2026-03-21_

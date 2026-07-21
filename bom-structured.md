# MSP430 Handheld Gaming Console — Structured BOM (Multi-Level)
_Revision: E — 2026-03-21_

A structured (multi-level) BOM expresses the product as a parent-child hierarchy. Each sub-assembly is broken down into its constituent components. **Qty** is per-parent (not aggregate) — to get total procurement quantities see `bom-flat.md`.

Level key: **L0** = top-level assembly · **L1** = sub-assembly · **L2** = purchased component

---

## L0 — MSP430 Handheld Gaming Console (Rev C, Prototype)

| Lvl | Item # | Assembly / Part | Manufacturer | MPN | Qty | UOM | Unit Price | Notes |
|-----|--------|----------------|-------------|-----|-----|-----|------------|-------|
| L0 | — | **MSP430 Handheld Gaming Console** | — | — | 1 | EA | — | Top-level assembly (Rev E, Prototype) |
| L1 | 1.0 | → MCU & Programming Module | — | — | 1 | EA | — | |
| L2 | 1.1 | → → LaunchPad MSP430G2553 dev board | Texas Instruments | MSP-EXP430G2ET | 1 | EA | $10.00 | Includes eZ-FET debugger, LED1/LED2, button S2 |
| L1 | 2.0 | → Display Module | — | — | 1 | EA | — | |
| L2 | 2.1 | → → 2.7" SSD1325 grayscale OLED SPI | Adafruit | #2674 | 1 | EA | $49.95 | 128×64, 16 gray levels, 3.3V SPI. Adafruit only. |
| L1 | 3.0 | → Memory Module | — | — | 1 | EA | — | Shared SPI bus (USCI_B0) |
| L2 | 3.1 | → → 128KB SPI SRAM (DIP-8) | Microchip | 23LC1024-I/P | 1 | EA | $2.50 | Framebuffer store + game state RAM |
| L2 | 3.2 | → → 16MB SPI NOR Flash, DIP breakout | Winbond / Adafruit | W25Q128JVSSIQ | 1 | EA | $2.95 | Sprites, music sequences, save data. Pre-assembled on Adafruit #5634 DIP PCB — plugs directly into breadboard. Standard SPI mode; USCI_B0 compatible. Adafruit only. |
| L2 | 3.3 | → → Capacitor, 0.1µF 50V ceramic (SRAM bypass) | Kemet | C320C104M5R5TA | 1 | EA | $0.10 | Place on SRAM VCC pin |
| L2 | 3.4 | → → Capacitor, 0.1µF 50V ceramic (Flash bypass) | Kemet | C320C104M5R5TA | 1 | EA | $0.10 | Place on Flash VCC pin |
| L1 | 4.0 | → Input Module | — | — | 1 | EA | — | SPI shift register + 8 buttons |
| L2 | 4.1 | → → 8-bit parallel-in shift register (DIP-16) | Texas Instruments | SN74HC165N | 1 | EA | $0.80 | Latches 8 button states in one SPI read |
| L2 | 4.2 | → → Tactile button, 6mm, 160gf (DIP-4) | Omron | B3F-1000 | 8 | EA | $0.20 | Left, Right, Down, Rotate CW, Rotate CCW, Drop, Start, Pause |
| L2 | 4.3 | → → Resistor, 10kΩ 1/4W (button pull-ups) | Yageo | CFR-25JB-52-10K | 8 | EA | $0.05 | One per button; 3.3V → resistor → SR input → button → GND |
| L2 | 4.4 | → → Capacitor, 0.1µF 50V ceramic (shift reg bypass) | Kemet | C320C104M5R5TA | 1 | EA | $0.10 | Place on SN74HC165N VCC pin |
| L1 | 5.0 | → Audio Module | — | — | 1 | EA | — | PWM tone via Timer_A → LM386 → speaker |
| L2 | 5.1 | → → Audio power amplifier (DIP-8) | Texas Instruments | LM386N-1/NOPB | 1 | EA | $1.00 | 20× gain default. Pins 1+8 open. |
| L2 | 5.2 | → → Speaker, 8Ω, 0.5W, 40mm | CUI Devices | CSS-04008 | 1 | EA | $2.00 | LM386 pin 5 → 220µF cap → 10Ω → speaker+ |
| L2 | 5.3 | → → Resistor, 1kΩ 1/4W (RC filter) | Yageo | CFR-25JB-52-1K0 | 1 | EA | $0.05 | PWM output → 1kΩ → 10µF cap → pot wiper → LM386 pin 3 |
| L2 | 5.4 | → → Resistor, 10Ω 1/4W (speaker series) | Yageo | CFR-25JB-52-10R | 1 | EA | $0.05 | Series protection on speaker output |
| L2 | 5.5 | → → Capacitor, 10µF 16V electrolytic (input coupling) | Nichicon | UVR1C100MDD | 1 | EA | $0.25 | RC filter output → LM386 pin 3 |
| L2 | 5.6 | → → Capacitor, 10µF 16V electrolytic (VCC bypass) | Nichicon | UVR1C100MDD | 1 | EA | $0.25 | LM386 pin 7 → GND |
| L2 | 5.7 | → → Capacitor, 220µF 16V electrolytic (output coupling) | Nichicon | UVR1C221MHD | 1 | EA | $0.50 | LM386 pin 5 → speaker |
| L2 | 5.8 | → → Potentiometer, 10kΩ audio/log taper, 9mm | Bourns | PTV09A-4020F-A103 | 1 | EA | $1.50 | Volume control; RC filter output → wiper → LM386 pin 3. A taper = audio/log. |
| L1 | 6.0 | → Power Module | — | — | 1 | EA | — | USB-C LiPo charge + 3.3V/5V rail |
| L2 | 6.1 | → → USB-C LiPo charger, 3.3V/5V output | Adafruit | #4410 | 1 | EA | $7.50 | Charges LiPo; provides regulated 3.3V to system. Adafruit only. |
| L2 | 6.2 | → → LiPo battery, 3.7V 2000mAh, JST-PH | Adafruit | #2011 | 1 | EA | $12.50 | Adafruit only. |
| L1 | 7.0 | → Prototyping Platform | — | — | 1 | EA | — | Temporary — replaced by custom PCB in final build |
| L2 | 7.1 | → → Long-pin breakaway header, 40-pos, 2.54mm | Samtec | TSW-140-07-G-S | 2 | EA | $3.50 | LaunchPad stacking headers |
| L2 | 7.2 | → → Solderless breadboard, 830 tie-points | — | — | 1 | EA | $10.00 | Elenco 9440 or equivalent |
| L2 | 7.3 | → → Jumper wire kit M-M 20cm, assorted | — | — | 1 | PK | $4.00 | |

---

## Build Phase Map

Phases indicate when each sub-assembly is added to the physical prototype. The structured BOM above is the complete product — not all sub-assemblies are present at every phase.

| Phase | Sub-assembly | Lessons |
|-------|-------------|---------|
| 1 | L1 1.0 MCU only (LaunchPad bare) | 01–05 |
| 2 | + L1 2.0 Display + L1 3.0 Memory + L1 7.0 Prototyping Platform | 06–10 |
| 3 | + L1 4.0 Input | 11–13 |
| 4 | + L1 5.0 Audio | 14–15 |
| 5 | + L1 6.0 Power (portable operation) | 16–20 |

---

## SPI Bus Allocation

All SPI devices share USCI_B0 on the MSP430G2553. CS pins are the only differentiators.

| Device | SCLK | MOSI | MISO | CS | DC | RST |
|--------|------|------|------|----|----|-----|
| SSD1325 OLED (2.1) | P1.5 | P1.7 | — | P2.0 | P2.1 | P2.2 |
| 23LC1024 SRAM (3.1) | P1.5 | P1.7 | P1.6 | P2.3 | — | — |
| W25Q32 Flash (3.2) | P1.5 | P1.7 | P1.6 | P2.4 | — | — |
| SN74HC165N input (4.1) | P1.5 | — | P1.6 | P2.5 (PL) | — | — |

> **Note:** P1.6 is also LED2 on the LaunchPad. Remove the LED2 jumper when using SPI.
> WP and HOLD pins on the 23LC1024 and W25Q32 should be tied to 3.3V.

---

## Spare Parts (Not in BOM)

| Part | Reason |
|------|--------|
| B3F-1000 × 4 extra | Tactile buttons wear with use |
| 10kΩ resistors × 4 extra | General debugging spares |
| 0.1µF ceramic × 2 extra | General bypass spares |
| 1.2kΩ + 10µF (optional) | Between LM386 pins 1–8 for 200× gain |
| 0.047µF + 1.2kΩ Zobel (optional) | LM386 output stability if speaker oscillates |

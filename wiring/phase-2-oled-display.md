# Phase 2 Hardware — SSD1325 OLED Display + Memory
*Added before Lesson 6*

## New Parts for Phase 2

| Part | Description | Source | Part # | ~Cost |
|------|-------------|--------|--------|-------|
| SSD1325 2.7" OLED | 128×64 grayscale SPI, 3.3V | Adafruit | #2674 | $49.95 |
| 23LC1024-I/P | 128KB SPI SRAM, DIP-8 | DigiKey | 23LC1024-I/P-ND | $2.50 |
| W25Q128JVSSIQ DIP breakout | 16MB SPI Flash, DIP breakout | Adafruit | #5634 | $2.95 |
| Samtec headers | Long-pin breakaway, 40-pos | DigiKey | SAM1029-40-ND | $3.50 |
| 0.1µF ceramic caps (×2) | Bypass caps for SRAM + Flash | DigiKey | 399-4151-ND | $0.20 |

## SPI Bus Overview

All three devices share the MSP430's USCI_B0 SPI bus. CS (chip select) pins differentiate them — only one CS may be LOW at a time.

| Device | SCLK | MOSI | MISO | CS | DC | RST |
|--------|------|------|------|----|----|-----|
| SSD1325 OLED | P1.5 | P1.7 | — | P2.0 | P2.1 | P2.2 |
| 23LC1024 SRAM | P1.5 | P1.7 | P1.6 | P2.3 | — | — |
| W25Q128 Flash | P1.5 | P1.7 | P1.6 | P2.4 | — | — |

## SSD1325 OLED Pin Connections

| OLED Pin | MSP430 Pin | Notes |
|----------|-----------|-------|
| GND | GND rail | |
| VCC | 3.3V rail | Do NOT use 5V |
| SCLK (D0) | P1.5 | UCB0CLK |
| MOSI (D1) | P1.7 | UCB0SIMO |
| RST | P2.2 | Toggle LOW on init |
| D/C | P2.1 | LOW = command, HIGH = data |
| CS | P2.0 | Active LOW chip select |

## 23LC1024 SRAM Pin Connections

| SRAM Pin | Signal | Connection |
|----------|--------|-----------|
| 1: CS# | SRAM_CS | P2.3 (active LOW) |
| 2: SO | MISO | P1.6 |
| 3: NC | — | Float |
| 4: VSS | GND | GND rail |
| 5: SI | MOSI | P1.7 |
| 6: SCK | SCLK | P1.5 |
| 7: HOLD# | — | Tie to VCC |
| 8: VCC | 3.3V | + 0.1µF bypass to GND |

## W25Q128 Flash (Adafruit #5634 DIP Breakout)

| Flash Pin | Signal | Connection |
|-----------|--------|-----------|
| 1: CS# | Flash_CS | P2.4 (active LOW) |
| 2: DO | MISO | P1.6 |
| 3: WP# | — | Tie to VCC |
| 4: GND | GND | GND rail |
| 5: VCC | 3.3V | + 0.1µF bypass to GND |
| 6: HOLD# | — | Tie to VCC |
| 7: CLK | SCLK | P1.5 |
| 8: DI | MOSI | P1.7 |

## Breadboard Layout (Phase 2 additions)

```
Panel A, rows 5-9:   23LC1024-I/P SRAM
Panel A, rows 12-16: W25Q128 Flash DIP breakout
Panel D, rows 5-12:  SSD1325 OLED 7-pin header

LaunchPad J2 connections for Phase 2:
  Pin 2 (P1.6) → SRAM SO, Flash DO     (MISO)
  Pin 3 (P1.7) → OLED DI, SRAM SI, Flash DI  (MOSI)
  Pin 4 (P2.0) → OLED CS
  Pin 5 (P2.1) → OLED D/C
  Pin 6 (P2.2) → OLED RST
  Pin 7 (P2.3) → SRAM CS#
  Pin 8 (P2.4) → Flash CS#

LaunchPad J1 connection:
  Pin 7 (P1.5) → OLED SCLK, SRAM SCK, Flash CLK  (SCLK)
```

## SSD1325 Init Sequence Notes

The SSD1325 uses an internal charge pump. Init sequence (covered in Lesson 9):
1. RST pulse: P2.2 LOW (≥100µs) → HIGH
2. CS LOW (P2.0), DC LOW (P2.1 = command mode)
3. Display off: `0xAE`
4. Set clock divide: `0xB3, 0xF1`
5. Set multiplex: `0xA8, 0x3F` (64 rows)
6. Set display offset: `0xA2, 0x4C`
7. Set start line: `0xA1, 0x00`
8. Remap: `0xA0, 0x52` (COM split, column remap)
9. Set VCC: `0xAB, 0x01`
10. Set contrast: `0x81, 0x70`
11. Set phase length: `0xB1, 0x11`
12. Set pre-charge: `0xBC, 0x08`
13. Set VCOMH: `0xBE, 0x07`
14. Master contrast: `0xA6`
15. Display on: `0xAF`

## Why External SRAM?

The SSD1325 framebuffer is 128×64×4 bits = 4,096 bytes. The MSP430G2553 has only 512 bytes total RAM — the full framebuffer doesn't fit on chip. The 23LC1024 provides 128KB off-chip RAM over SPI, used as a backing framebuffer. The firmware writes partial column updates (strip-rendering) to minimize SPI traffic.

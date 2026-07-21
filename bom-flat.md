# MSP430 Handheld Gaming Console — Flat BOM (Single-Level)
_Revision: E — 2026-03-21_

A flat (single-level) BOM lists every component needed to build the complete assembly in one table at equal hierarchy depth. Quantities are **aggregate totals** across all uses. No parent-child relationships are expressed here — see `bom-structured.md` for the product breakdown hierarchy.

---

| Item # | Manufacturer | MPN | Description | Pkg | Qty | UOM | Unit Price (USD) | Ext Price (USD) | Preferred Vendor | Vendor Part # | Lifecycle | Notes |
|--------|-------------|-----|-------------|-----|-----|-----|-----------------|-----------------|-----------------|---------------|-----------|-------|
| 001 | Texas Instruments | MSP-EXP430G2ET | MSP430G2553 LaunchPad dev board | — | 1 | EA | $10.00 | $10.00 | Mouser | 595-MSP-EXP430G2ET | Active | Includes eZ-FET lite debugger, LED1/LED2, button S2 |
| 002 | Adafruit | #2674 | 2.7" 128×64 SSD1325 grayscale OLED SPI 3.3V | — | 1 | EA | $49.95 | $49.95 | Adafruit | 2674 | Active | adafruit.com only |
| 003 | Microchip | 23LC1024-I/P | 128KB SPI SRAM | DIP-8 | 1 | EA | $2.50 | $2.50 | DigiKey | 23LC1024-I/P-ND | Active | External framebuffer + game-state RAM |
| 004 | Winbond / Adafruit | W25Q128JVSSIQ | 16MB SPI NOR Flash on DIP breakout | DIP breakout | 1 | EA | $2.95 | $2.95 | Adafruit | 5634 | Active | Pre-assembled SOIC-8 on DIP PCB — plug directly into breadboard. Standard SPI mode compatible with MSP430 USCI_B0. adafruit.com only. |
| 005 | Texas Instruments | SN74HC165N | 8-bit parallel-in serial-out shift register | DIP-16 | 1 | EA | $0.80 | $0.80 | DigiKey | 296-8251-5-ND | Active | Button input latch |
| 006 | Omron | B3F-1000 | 6mm momentary tactile button, 4-pin, 160gf | Through-hole | 12 | EA | $0.20 | $2.40 | DigiKey | B3F-1000-ND | Active | 8 used, 4 spares. Tactile switches wear — order extra. |
| 007 | Texas Instruments | LM386N-1/NOPB | Low-voltage audio power amplifier | DIP-8 | 1 | EA | $1.00 | $1.00 | DigiKey | LM386N-1/NOPB-ND | Active | 20× gain default; 200× with external network |
| 008 | CUI Devices | CSS-04008 | Speaker, 8Ω, 0.5W, 40mm | — | 1 | EA | $2.00 | $2.00 | DigiKey | 102-SP-3605-ND | Active | 8Ω load for LM386 |
| 009 | Samtec | TSW-140-07-G-S | Long-pin breakaway header, 40-pos, 2.54mm | Through-hole | 2 | EA | $3.50 | $7.00 | DigiKey | SAM1029-40-ND | Active | LaunchPad stacking headers |
| 010 | Adafruit | #4410 | USB-C LiPo charger, 3.3V/5V output | — | 1 | EA | $7.50 | $7.50 | Adafruit | 4410 | Active | adafruit.com only |
| 011 | Adafruit | #2011 | 3.7V 2000mAh LiPo battery, JST-PH | — | 1 | EA | $12.50 | $12.50 | Adafruit | 2011 | Active | adafruit.com only |
| 012 | Yageo | CFR-25JB-52-10K | Resistor, 10kΩ, 1/4W, 5%, carbon film | Axial | 12 | EA | $0.05 | $0.60 | DigiKey | 10KEBK-ND | Active | Button pull-ups (8 used) + spares |
| 013 | Yageo | CFR-25JB-52-1K0 | Resistor, 1kΩ, 1/4W, 5%, carbon film | Axial | 2 | EA | $0.05 | $0.10 | DigiKey | 1.0KEBK-ND | Active | PWM RC filter |
| 014 | Yageo | CFR-25JB-52-10R | Resistor, 10Ω, 1/4W, 5%, carbon film | Axial | 2 | EA | $0.05 | $0.10 | DigiKey | 10EBK-ND | Active | Speaker series resistor |
| 015 | Kemet | C320C104M5R5TA | Capacitor, 0.1µF, 50V, ceramic | Axial | 4 | EA | $0.10 | $0.40 | DigiKey | 399-4151-ND | Active | Bypass caps: SRAM, Flash, shift reg, spare |
| 016 | Nichicon | UVR1C100MDD | Capacitor, 10µF, 16V, electrolytic | Radial 2.5mm | 3 | EA | $0.25 | $0.75 | DigiKey | 493-1081-ND | Active | Audio input coupling + VCC bypass |
| 017 | Nichicon | UVR1C221MHD | Capacitor, 220µF, 16V, electrolytic | Radial 5mm | 1 | EA | $0.50 | $0.50 | DigiKey | 493-1377-ND | Active | LM386 output coupling |
| 018 | — | — | Full-size solderless breadboard, 830 tie-points | — | 1 | EA | $10.00 | $10.00 | Amazon | — | — | Elenco 9440 or equivalent |
| 019 | — | — | Jumper wire kit M-M 20cm, assorted colours | — | 1 | PK | $4.00 | $4.00 | Amazon | — | — | |
| 020 | Bourns | PTV09A-4020F-A103 | Potentiometer, 10kΩ, audio/log taper, 9mm, 20mm shaft | Through-hole | 1 | EA | $1.50 | $1.50 | DigiKey | PTV09A-4020F-A103-ND | Active | Volume control; RC filter output → wiper → LM386 pin 3. Use A taper, not B. |

---

## Cost Summary

| Category | Ext Price |
|----------|-----------|
| MCU & LaunchPad | $10.00 |
| Display | $49.95 |
| Memory (SRAM + Flash breakout) | $5.45 |
| Input (shift reg + buttons) | $3.20 |
| Audio (amp + speaker + pot) | $4.50 |
| Power (charger + battery) | $20.00 |
| Passives (R + C) | $2.45 |
| Prototyping (headers + breadboard + wire) | $21.00 |
| **Total (est., excl. shipping)** | **$116.55** |

---

## Vendor Split

| Vendor | Items | Est. Subtotal |
|--------|-------|--------------|
| Adafruit (adafruit.com) | 002, 004, 010, 011 | $72.90 |
| DigiKey (digikey.com) | 003, 005, 006, 007, 008, 009, 012–017, 020 | $19.65 |
| Mouser (mouser.com) | 001 | $10.00 |
| Amazon / generic | 018, 019 | $14.00 |

> DigiKey part numbers are catalog references — search the MPN directly if a number returns no result.
> Items 002, 004, 010, 011 are available from Adafruit only.
> Item 004 (W25Q128JVSSIQ): Adafruit #5634 is pre-assembled on a DIP breakout PCB — plugs directly into breadboard, no adapter or soldering required.

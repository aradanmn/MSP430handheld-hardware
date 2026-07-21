# MSP430 Handheld — Hierarchical Schematic Set

A Framework-style hierarchical KiCad 9 schematic for the MSP430G2553 handheld,
modelled on the [Framework Desktop mainboard schematic](https://github.com/FrameworkComputer/Framework-Desktop):
a top-level **Block Diagram / Interfaces** sheet plus one detailed sheet per
functional block.

## Open it

Open `msp430_handheld.kicad_pro` (or the root `msp430_handheld.kicad_sch`) in
**KiCad 9.x**. The root sheet is the interconnect overview; double-click a block
to descend into its detail sheet.

## Sheets

| Page | File | Contents |
|------|------|----------|
| 1 | `msp430_handheld.kicad_sch` | **Block Diagram** — MCU-centric interconnect overview, connector/bus legend, power-rail legend |
| 2 | `sheet_mcu.kicad_sch` | MSP430G2553 + decoupling; SPI bus master, all CS/control GPIO |
| 3 | `sheet_display.kicad_sch` | Adafruit #2674 SSD1325 OLED module (SPI) |
| 4 | `sheet_memory.kicad_sch` | 23LC1024 SRAM + W25Q128 NOR Flash (shared SPI) |
| 5 | `sheet_input.kicad_sch` | 74HC165 PISO shift register + 8 buttons + 10k pull-ups |
| 6 | `sheet_audio.kicad_sch` | LM386 PWM audio (5 V rail) + RC filter + volume pot + speaker |
| 7 | `sheet_power.kicad_sch` | USB-C charger + 5 V boost + 3.3 V buck-boost + LiPo + power switch |

## Conventions

- **Signal flow** left→right, **power** top→bottom.
- **Cross-sheet nets use global labels** (`SCK`, `MOSI`, `MISO`, `OLED_CS`,
  `SRAM_CS`, `FLASH_CS`, `SH_LD`, `PWM_OUT`, …) — they connect across all sheets
  of the hierarchy, so no hierarchical sheet-pins are needed.
- **Power rails** reflect BOM Rev F: **+3V3** for all logic (MCU, OLED, SRAM,
  Flash, 74HC165), **+5V** for the LM386, **GND** common, **VBAT** from the cell.
- The shared SPI bus is USCI_B0: `SCK`=P1.5, `MOSI`=P1.7, `MISO`=P1.6; chip
  selects on P2.0–P2.5.

## Regenerating

The schematic is generated, not hand-drawn. Symbols are harvested from the
component-level schematic `../msp430_gameboy.kicad_sch` (this repo's validated
KiCad-9 symbols) — no external KiCad libraries are required to regenerate.

```sh
python3 ../../scripts/gen_handheld_hier.py
```

Do not hand-edit the generated `.kicad_sch` files or patch the generator's
layout in place — change the source data and regenerate.

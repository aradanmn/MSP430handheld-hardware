# Handheld MSP430 — Hardware

Hardware design for a DIY handheld game console built around the
**MSP430G2553** microcontroller: bill of materials, breadboard layout, KiCad 9
schematic, and the engineering design history.

This repo is the **hardware side** of the project. The firmware and the
26-lesson MSP430 assembly course that builds it live in the companion
software repo: **[aradanmn/MSP430handheld-firmware](https://github.com/aradanmn/MSP430handheld-firmware)**.

## Components

| Component | Part | Purpose |
|-----------|------|---------|
| MCU | MSP430G2553 (LaunchPad MSP-EXP430G2) | Main controller |
| Display | SSD1325 2.7″ OLED, 128×64 grayscale SPI | Video output |
| SRAM | 23LC1024-I/P (128 KB SPI, DIP-8) | Off-chip framebuffer backing store |
| Flash | W25Q128 (16 MB SPI, DIP breakout, Adafruit #5634) | Asset / level storage |
| Shift register | SN74HC165N (DIP-16) | 8-button input over the SPI bus |
| Audio amp | LM386N-1 (DIP-8) | PWM → speaker |
| Speaker | SP-3605, 8 Ω | Audio output |
| LiPo charger | Adafruit 4410 (USB-C) | Battery charging |
| Battery | Adafruit 2011 (3.7 V LiPo, JST-PH) | Power |

Full ordering detail: [`bom-structured.md`](bom-structured.md),
[`bom-flat.md`](bom-flat.md), [`bom-order.csv`](bom-order.csv).

## Bus & pins

All SPI peripherals share the MSP430's **USCI_B0** bus and are selected by
individual chip-select lines (only one CS low at a time):

| Signal | MSP430 pin |
|--------|-----------|
| SCLK | P1.5 (UCB0CLK) |
| MOSI | P1.7 (UCB0SIMO) |
| MISO | P1.6 (UCB0SOMI) |

The authoritative per-signal chip-select and control assignments (rev 5.0) are
in the schematic `title_block` of
[`schematic/msp430_gameboy.kicad_sch`](schematic/msp430_gameboy.kicad_sch),
and the per-phase wiring is broken out under [`wiring/`](wiring/).

## Repository layout

```
MSP430handheld-hardware/
├── bom-flat.md / bom-structured.md / bom-order.csv   Bill of materials
├── schematic/     KiCad 9 schematic (rev 5.0) + timestamped snapshots
├── breadboard/    Elenco 9440 layout — breadboard_layout.html + breadboard_guide.md
├── scripts/       Schematic generators — gen_kicad7.py (current), gen_kicad6.py (prior)
├── wiring/        Per-build-phase wiring guides (phase-1 … phase-4)
├── datasheets/    Component datasheets + pin-function reference (see its README)
├── notes/         Versioned engineering notes (yyyymmdd_HHmmss.md) + SESSION_NOTES.md
└── logs/          Session conversation logs
```

## Build phases

Hardware is added incrementally as the course progresses:

- [`wiring/phase-1-launchpad-only.md`](wiring/phase-1-launchpad-only.md) — bare LaunchPad (Lessons 1–5)
- [`wiring/phase-2-oled-display.md`](wiring/phase-2-oled-display.md) — OLED + SRAM + Flash on the SPI bus
- [`wiring/phase-3-buttons-shift-register.md`](wiring/phase-3-buttons-shift-register.md) — 8-button SN74HC165N input
- [`wiring/phase-4-audio.md`](wiring/phase-4-audio.md) — LM386 amplifier + speaker

## Schematic

The KiCad 9 schematic is generated programmatically rather than drawn by hand.

```bash
python3 scripts/gen_kicad7.py     # writes schematic/msp430_gameboy.kicad_sch
```

Optional validation: `pip install kiutils`.

- Current: [`schematic/msp430_gameboy.kicad_sch`](schematic/msp430_gameboy.kicad_sch) — rev 5.0 (adds OLED CS/DC/RST, SRAM, Flash)
- Generator: [`scripts/gen_kicad7.py`](scripts/gen_kicad7.py) (current), `scripts/gen_kicad6.py` (prior)
- Timestamped snapshots are kept alongside the current file for history.

## Design history

The [`notes/`](notes/) and [`logs/`](logs/) directories hold versioned
engineering notes and session logs from the breadboard / rev 4.0 bring-up —
the KiCad 9 format lessons, the grid-alignment debugging that fixed
"nothing connected", component-position tables, and net lists. Preserved
verbatim as design history.

## Status

- [x] BOM (DigiKey, ~$53 core)
- [x] Breadboard layout (Elenco 9440, 4-panel)
- [x] KiCad 9 schematic — rev 5.0 (grid-aligned, connections verified)
- [ ] PCB layout
- [ ] Enclosure

# Handheld MSP430 Game Boy Clone

A DIY handheld game console built around the **MSP430G2553** microcontroller.

## Hardware

| Component | Part | Purpose |
|-----------|------|---------|
| MCU | MSP430G2553 (LaunchPad MSP-EXP430G2) | Main controller |
| Shift register | SN74HC165N (DIP-16) | 8-button input via SPI |
| Audio amp | LM386N-1 (DIP-8) | PWM → speaker |
| Display | 0.96″ OLED SPI 128×64 | Video output |
| LiPo charger | Adafruit 4410 (USB-C) | Battery charging |
| Battery | Adafruit 2011 (3.7V 2Ah JST-PH) | Power |
| Speaker | SP-3605 8Ω | Audio output |

## Repository Layout

```
handheld-msp430/
├── schematic/          KiCad 9 schematic files
│   └── msp430_gameboy.kicad_sch
├── breadboard/         Breadboard layout (Elenco 9440)
│   ├── breadboard_layout.html  (SVG visual)
│   └── breadboard_guide.md     (wiring reference)
├── scripts/            Schematic generator scripts
│   ├── gen_kicad7.py   (current — rev 4.0, grid-aligned)
│   └── gen_kicad6.py   (prior version)
├── notes/              Versioned engineering notes (yyyymmdd_HHmmss.md)
├── logs/               Session conversation logs
└── README.md
```

## Connections

| Signal | MSP430 Pin | Destination |
|--------|-----------|-------------|
| SCK | P1.5 | SN74HC165N CLK, OLED CLK |
| MISO | P1.6 | SN74HC165N QH (serial out) |
| MOSI | P1.7 | OLED MOSI |
| SH/LD# | P2.4 | SN74HC165N SH_LD |
| PWM audio | P1.2 | 1kΩ+100nF → LM386N IN− |
| ADC | P1.3 | 10kΩ pot wiper |

## Schematic Generator

The schematic is generated programmatically (not drawn by hand). To regenerate:

```bash
python3 scripts/gen_kicad7.py
# writes schematic/msp430_gameboy.kicad_sch
```

Requires Python 3 and optionally `kiutils` for validation:
```bash
pip install kiutils
```

## Status

- [x] DigiKey BOM (~$53)
- [x] Breadboard layout (Elenco 9440, 4-panel)
- [x] KiCad 9.0.7 schematic — rev 4.0 (grid-aligned, all connections verified)
- [ ] PCB layout
- [ ] Firmware

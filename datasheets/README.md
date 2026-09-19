# Datasheets

Reference datasheets for the BOM components in `../bom-structured.md`, downloaded
from official manufacturer sites where possible. Pin *assignments* (which
MSP430 pin each signal connects to) are the existing, authoritative source in
this repo — `../bom-structured.md`'s "SPI Bus Allocation" table and
`../wiring/phase-*.md`. The tables below add pin *function* names (what each
physical IC/module pin is called on the part itself), pulled from these
datasheets, for parts not already broken out pin-by-pin elsewhere in the repo.

**Not included on purpose:** the MSP430G2553 datasheet (SLAS735) and the
MSP430x2xx Family User's Guide (SLAU144). The firmware repo's `CLAUDE.md`
deliberately has the student look those up themselves — see that repo's
"Datasheet References" section. Everything below is peripheral/module
documentation, not MCU/ISA reference, so it doesn't touch that rule.

## Index

| BOM # | Part | Manufacturer | MPN | File | Source |
|-------|------|--------------|-----|------|--------|
| 1.1 | MSP-EXP430G2ET LaunchPad | Texas Instruments | MSP-EXP430G2ET | [ti-slau318-launchpad-guide.pdf](ti-slau318-launchpad-guide.pdf) | [ti.com/lit/ug/slau318g](https://www.ti.com/lit/ug/slau318g/slau318g.pdf) |
| 2.1 | SSD1325 OLED controller (in Adafruit #2674) | Solomon Systech | SSD1325 | [solomon-ssd1325.pdf](solomon-ssd1325.pdf) | [displayfuture.com mirror](https://www.displayfuture.com/Display/datasheet/controller/SSD1325.pdf) — Solomon Systech doesn't host its own public copy; [Adafruit product page](https://www.adafruit.com/product/2674) for the module itself |
| 3.1 | 23LC1024-I/P SPI SRAM | Microchip | 23LC1024-I/P | [microchip-23lc1024.pdf](microchip-23lc1024.pdf) | [microchip.com](https://ww1.microchip.com/downloads/aemDocuments/documents/MPD/ProductDocuments/DataSheets/23A102423LC1024-1-Mbit-SPI-Serial-SRAM-with-SDI-SQI-Interface-20005142.pdf) |
| 3.2 | W25Q128JVSSIQ SPI Flash (Adafruit #5634 breakout) | Winbond | W25Q128JVSSIQ | [winbond-w25q128jv.pdf](winbond-w25q128jv.pdf) | [winbond.com](https://www.winbond.com/resource-files/W25Q128JV%20RevH%2003102021%20Plus.pdf) |
| 4.1 | SN74HC165N shift register | Texas Instruments | SN74HC165N | [ti-sn74hc165.pdf](ti-sn74hc165.pdf) | [ti.com](https://www.ti.com/lit/ds/symlink/sn74hc165.pdf) |
| 4.2 | B3F-1000 tactile button | Omron | B3F-1000 | [omron-b3f-series.pdf](omron-b3f-series.pdf) | [omronfs.omron.com](https://omronfs.omron.com/en_US/ecb/products/pdf/en-b3f.pdf) (B3F series datasheet; -1000 is one variant in it) |
| 5.1 | LM386N-1/NOPB audio amp | Texas Instruments | LM386N-1/NOPB | [ti-lm386.pdf](ti-lm386.pdf) | [ti.com](https://www.ti.com/lit/ds/symlink/lm386.pdf) |
| 5.2 | CSS-04008 speaker | CUI Devices | CSS-04008 | *(none — see note below)* | — |
| 5.8 | PTV09A-4020F-A103 potentiometer | Bourns | PTV09A-4020F-A103 | [bourns-ptv09-series.pdf](bourns-ptv09-series.pdf) | [bourns.com](https://www.bourns.com/docs/product-datasheets/PTV09.pdf) (PTV09 series datasheet; -A103 is one variant in it) |
| 6.1 | Micro-Lipo USB-C charger | Adafruit | #4410 | [adafruit-microlipo-charger-guide.pdf](adafruit-microlipo-charger-guide.pdf) + [microchip-mcp73831.pdf](microchip-mcp73831.pdf) | Adafruit's own [learning guide](https://cdn-learn.adafruit.com/downloads/pdf/adafruit-microlipo-and-minilipo-battery-chargers.pdf) for the board; charge-controller IC is Microchip [MCP73831](https://ww1.microchip.com/downloads/en/DeviceDoc/MCP73831-Family-Data-Sheet-DS20001984H.pdf) |
| 6.2 | LiPo battery, 3.7V 2000mAh | Adafruit | #2011 | *(none — see note below)* | [adafruit.com/product/2011](https://www.adafruit.com/product/2011) |
| 6.3 | PowerBoost 500 Basic | Adafruit | #1903 | [adafruit-powerboost-500-guide.pdf](adafruit-powerboost-500-guide.pdf) + [ti-tps61090.pdf](ti-tps61090.pdf) | Adafruit's own [learning guide](https://cdn-learn.adafruit.com/downloads/pdf/adafruit-powerboost.pdf) for the board; boost-converter IC is TI [TPS61090](https://www.ti.com/lit/ds/symlink/tps61090.pdf) |
| 6.4 | S7V8F3 buck-boost regulator | Pololu | S7V8F3 | *(none — see note below)* | [pololu.com/product/2122](https://www.pololu.com/product/2122), [resources](https://www.pololu.com/product/2122/resources) |
| 6.5 | EG1218 SPDT slide switch | E-Switch | EG1218 | [eswitch-eg1218.pdf](eswitch-eg1218.pdf) | Manufacturer doesn't host a direct public copy; mirrored via [Octopart](https://datasheet.octopart.com/EG1218-E-Switch-datasheet-13521068.pdf) |

## Notes on parts without a downloaded datasheet

- **5.2 CSS-04008 (speaker):** this exact part number doesn't resolve to a real
  CUI Devices/Same Sky catalog entry — searching turns up neighboring parts
  like `CSS-40408N` (40mm, 8Ω) but nothing named `CSS-04008`. Rather than
  attach a datasheet for a part that might not be the one actually in hand,
  this is flagged here for you to double check against whatever's physically
  on hand or was actually ordered, and fix either the BOM or this entry once
  confirmed.
- **6.2 Adafruit #2011 (battery):** Adafruit doesn't publish a standalone
  datasheet PDF for this cell — its specs live only on the
  [product page](https://www.adafruit.com/product/2011). Key numbers from
  there: 3.7V nominal, 2000mAh, JST-PH connector, built-in protection circuit,
  cutoff at 3.0V.
- **6.4 Pololu S7V8F3:** Pololu doesn't publish the specific regulator IC
  datasheet for this board (their docs reference the TI TPS6300x family only
  generically). The board's own spec sheet and schematic are on its
  [resources page](https://www.pololu.com/product/2122/resources) instead.

## Pin references

Only adding function names for parts not already pin-mapped in
`../wiring/phase-*.md`. See those files for the authoritative MSP430-side
connections — this just documents what each physical pin is *called* on the
part.

### 23LC1024 SPI SRAM (DIP-8) — see also `wiring/phase-2-oled-display.md`

| Pin | Name | Function |
|-----|------|----------|
| 1 | CS# | Chip select, active low |
| 2 | SO | Serial data out (MISO) |
| 3 | NC | No connect |
| 4 | VSS | Ground |
| 5 | SI | Serial data in (MOSI) |
| 6 | SCK | Serial clock |
| 7 | HOLD# | Hold — tie to VCC if unused |
| 8 | VCC | +3.3V supply |

### W25Q128JVSSIQ SPI Flash (Adafruit #5634 breakout) — see also `wiring/phase-2-oled-display.md`

| Pin | Name | Function |
|-----|------|----------|
| 1 | CS# | Chip select, active low |
| 2 | DO (IO1) | Data out (MISO in standard SPI mode) |
| 3 | WP#/IO2 | Write-protect — tie to VCC in standard SPI mode |
| 4 | GND | Ground |
| 5 | DI (IO0) | Data in (MOSI in standard SPI mode) |
| 6 | CLK | Serial clock |
| 7 | HOLD#/IO3 | Hold — tie to VCC in standard SPI mode |
| 8 | VCC | +3.3V supply |

### SN74HC165N shift register (DIP-16) — full pinout already in `wiring/phase-3-buttons-shift-register.md`

Datasheet adds the internal pin names that doc abbreviates:

| Pin | Datasheet name | Meaning |
|-----|----------------|---------|
| 1 | SH/LD# | Shift/Load — LOW latches parallel inputs, HIGH shifts |
| 2 | CLK | Serial clock |
| 9 | Q7 (QH) | Serial data output |
| 10 | CLK INH | Clock inhibit — tie LOW to always allow clocking |
| 15 | SER | Serial input — for daisy-chaining another '165; tie LOW/GND if unused |
| 16 | VCC | +3.3V supply |
| 8 | GND | Ground |
| 3–6, 11–14 | D0–D7 (A–H) | Parallel data inputs |

### LM386N-1 audio amp (DIP-8) — see also `wiring/phase-4-audio.md`

| Pin | Name | Function |
|-----|------|----------|
| 1 | GAIN | Gain set (open = 20x default; per datasheet, resistor+cap to pin 8 raises gain to 200x) |
| 2 | −IN | Inverting input — ground in this design |
| 3 | +IN | Non-inverting input — audio signal in |
| 4 | GND | Ground |
| 5 | OUT | Amplified output to speaker |
| 6 | V+ | Supply (4–12V typ.; **use the 5V rail, not 3.3V — datasheet minimum is 4V**) |
| 7 | BYPASS | Ripple bypass — decouple to GND |
| 8 | GAIN | Gain set (paired with pin 1) |

### MCP73831 charge-controller IC (inside Adafruit #4410) — SOT-23-5

| Pin | Name | Function |
|-----|------|----------|
| 1 | PROG | Charge-current programming (sets via resistor; fixed on the Adafruit board) |
| 2 | VSS | Ground |
| 3 | VBAT | Battery output |
| 4 | STAT | Open-drain charge-status output (drives the onboard LED) |
| 5 | VDD | USB input power |

### TPS61090 boost-converter IC (inside Adafruit #1903 PowerBoost 500 Basic)

See the Adafruit learning guide for the board-level pinout (`EN`, `LBO`,
`USB`/`5V`, `GND`, `BAT`) — those board pins map internally to the TPS61090's
QFN pins per the guide's schematic; not repeated here since the board-level
names are what you actually wire to.

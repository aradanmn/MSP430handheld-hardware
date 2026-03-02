# MSP430G2553 Game Boy — Session Notes
_Last updated: 2026-03-01 (session 2)_

## Project Overview
Building an MSP430G2553-based Game Boy clone. Parts ordered from DigiKey (~$53 total).
Key components: MSP430G2553 LaunchPad (MCU), SN74HC165N (8-button shift register), LM386N-1 (audio amp), 0.96" OLED (SPI), Adafruit 4410 LiPo charger, 3.7V LiPo.

## Deliverables (in /outputs/)
- `msp430_gameboy.kicad_sch` — KiCad 8.0 schematic (current working version)
- `breadboard_layout.html` — SVG breadboard visual
- `breadboard_guide.md` — Wiring reference

## Schematic Current State
**Opens in KiCad 8** ✅ — Single `(kicad_sch ...)` block, `(lib_symbols ...)` embedded with 11 symbols, 63 placed symbols, 45 labels, 17 no-connects. Paren-balanced.

**Applied fixes (session 2)** ✅:
- `label()`: now always `justify left` + `fields_autoplaced yes` (KiCad 8 standard)
- `placed_sym()`: Reference/Value properties now hidden (`hide yes`) — no more IC-body text overlap
- Wire stubs added: every label is 2.54mm off the pin endpoint with an explicit wire connecting them

**Remaining visual issues** (not yet tested):

### 1. Text Overlapping
**Root cause**: `placed_sym()` puts Reference at `(cx+2, cy-2.54)` and Value at `(cx+2, cy+2.54)` — right inside the IC body, overlapping pin labels (only 1.27mm gap from nearest pin).

**Fix needed in `placed_sym()` in gen_kicad5.py**:
```python
# Move ref ABOVE the IC body, value BELOW
body_h = 13.97  # for MSP430 (10 pins/side); compute per component
ref_y = cy - body_h - 3.0   # above IC
val_y = cy + body_h + 3.0   # below IC
# Also hide ref/value inside symbol lib definitions (set hide yes on property effects)
```
Or simpler: just add `(hide yes)` to all Reference/Value effects in placed symbols since net labels already identify everything.

### 2. Nothing Connected (Labels)
**Root cause**: Labels use `(justify right)` for rot=180, but KiCad 8 expects `(justify left)` for ALL label rotations. Also missing `(fields_autoplaced yes)`.

**Fix in `label()` function in gen_kicad5.py**:
```python
def label(net, x, y, rot=0):
    # KiCad 8: always justify left, rotation handles visual direction
    return (f'(label "{net}" (at {x:.4f} {y:.4f} {rot})'
            f' (fields_autoplaced yes)'
            f' (effects (font (size 1.27 1.27)) (justify left))'
            f' (uuid "{uid()}"))')
```

### 3. Power Symbols May Need Wire Stubs
If labels still don't connect after justify fix, add explicit 2.54mm wire stubs:
```python
# Instead of just placing a label at pin endpoint, draw a wire stub first
# e.g., for a left-side pin at (wx, wy), label at (wx - 2.54, wy):
wir(wx, wy, wx - 2.54, wy)
lbl('NET', wx - 2.54, wy, rot=180)
```

## Generator Script
**Active file**: `/tmp/gen_kicad5.py` (latest, fixes dual-kicad_sch and missing lib_symbols)

### Key architecture of gen_kicad5.py
- `ic_sym(name, left_pins, right_pins, body_hw=5.08)` → builds symbol + `pin_dict`
- `pw(cx, cy, lx, ly)` → world coord using **Y-FLIP**: `(cx+lx, cy-ly)`
  - KiCad symbol Y is UP (math coords); schematic Y is DOWN (screen coords)
- `pin_world(comp_xy, pin_dict, pin_name)` → calls `pw()`
- Connections use `lbl()`, `pwr()`, `nc()` all called with `pin_world(...)` coords

### Component positions (schematic world coords)
| Ref | Component | World (cx, cy) |
|-----|-----------|----------------|
| U1 | MSP430G2553 | (170, 120) |
| U2 | SN74HC165N | (60, 120) |
| U3 | LM386N-1 | (270, 120) |
| LS1 | Speaker | (315, 120) |
| J1 | OLED connector | (60, 50) |
| J2 | LiPo charger | (320, 50) |
| RV1 | Volume pot | (60, 195) |
| RV2 | ADC pot | (270, 195) |
| R1 | 1kΩ RC filter | (205, 155) |
| C1 | 100nF RC filter | (205, 170) |
| C2 | 100nF decoupling | (150, 90) |
| SW1-8 | Buttons | x=20, y=65..135 |
| R2-9 | 10k pull-ups | x=42, y=65..135 |

### Pin coordinate formula
For component at `(cx, cy)`, pin at symbol-local `(lx, ly)`:
- `world_x = cx + lx`
- `world_y = cy - ly` ← Y is FLIPPED

Pin endpoints: `lx = ±(body_hw + 2.54)` = `±7.62` for most ICs (body_hw=5.08)

## Net Connections Summary
| Signal | From | To |
|--------|------|----|
| SCK | U1 P1.5 | U2 CLK, J1 pin3 |
| MISO | U1 P1.6 | U2 QH |
| MOSI | U1 P1.7 | J1 pin4 |
| SH_LD | U1 P2.4 | U2 SH_LD |
| PWM_OUT | U1 P1.2 | R1 pin1 |
| AUDIO_IN | R1 pin2, C1 pin1 | U3 IN- |
| ADC_POT | U1 P1.3 | RV2 wiper |
| SPK_OUT | U3 OUTPUT | LS1 pin1 |
| BTN_A..H | U2 A-H inputs | SW1-8 via R2-9 pull-ups |
| VOL_WIPER | RV1 wiper | (future: P1.3 if needed) |

## KiCad 8 Format Notes (hard-won lessons)
- Single `(kicad_sch ...)` block — NO duplicate blocks
- `(lib_symbols ...)` MUST be inside `(kicad_sch ...)`, immediately after `(title_block ...)`
- `(sheet_instances (path "/" (page "1")))` at the very END
- No `(sheets ...)` or `(symbol_instances ...)` blocks (those are KiCad 5/6 artifacts)
- Version string: `20231120` for KiCad 8.0
- Labels: `(label "NET" (at x y rot) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify left)) (uuid "..."))`
- Power symbols placed at EXACT pin endpoint world coords
- Paren balance must be 0

## Next Session Tasks
1. Open schematic and check visually — text overlap and connection issues should be resolved
2. Run KiCad ERC (Inspect → Electrical Rules Checker) — should show 0 errors
3. If pin labels still crowded: reduce symbol pin-name font to 0.762mm in `ic_sym()` `(size 1.016 1.016)` → `(size 0.762 0.762)`
4. If any wires/labels still misaligned: the `lbl()` wire-stub approach (pin→stub→label) is in gen_kicad5.py and easy to adjust

## Quick Resume Command
```bash
python3 /tmp/gen_kicad5.py   # regenerate schematic
# Then open: /sessions/.../mnt/outputs/msp430_gameboy.kicad_sch
```

# Hardware BOM Review — Power & Compatibility

_Reviewed 2026-07-21 against BOM Rev E. Changes applied in BOM Rev F._

## Scope

Reviewed the three BOM files, the KiCad schematic, and the wiring guides for
**incompatibilities and missing components** that would prevent building a working
MSP430G2553-based handheld. Assessed against two targets:

- **Breadboard bring-up** — LaunchPad + Adafruit breakout modules, USB-powered.
- **Portable handheld** — self-powered from the LiPo, unplugged.

**Bottom line:** the electronics (MCU, display, memory, input, audio signal chain)
are compatible and well specified, but **the power subsystem could not actually run
the device**. The BOM had no voltage regulator, so there was no valid way to power
the 3.3 V logic from the battery, and the audio amplifier had no supply rail it
could operate on. Three parts were added and two descriptions corrected (Rev F).

---

## Critical findings

### 1. No voltage regulator in the BOM — the battery cannot power the system

Item 010 (Adafruit **#4410**) was described as *"USB-C LiPo charger, 3.3V/5V
output."* Adafruit's product page shows #4410 is the **Micro-Lipo *charger only***:
it charges a cell over USB-C and its output is the **raw cell voltage (~3.0–4.2 V),
not a regulated rail**. Nothing else in the BOM regulated voltage.

Consequence for the portable build: the only power source feeding the system was the
bare LiPo.

### 2. Raw LiPo over-volts the MCU

The MSP430G2553 absolute-maximum VCC is **3.6 V**; a fully charged LiPo is **4.2 V**.
The structured BOM's power note ("VCC out → VCC rail") wired the cell straight to the
3.3 V rail — that exceeds the MCU's abs-max and would also over-stress the OLED, SRAM,
Flash, and shift register. → **a regulated 3.3 V supply is required and was missing.**

### 3. The LM386 audio amp had no rail it could run on

Per the TI LM386 datasheet, the **LM386N-1 minimum supply voltage is 4 V** (operating
range 4–12 V). The BOM and wiring guide put the amp's V+ on the 3.3 V "VCC" rail —
**below its minimum**, so audio would not work. There was no 5 V (or any ≥4 V) rail
anywhere in the design. This breaks audio on **both** targets: even on the bench, the
LaunchPad's on-board LDO only exposes 3.3 V on the standard headers.

---

## Fix — recommended power architecture (applied in Rev F)

Two regulators derive both required rails from the single LiPo, and a master switch
gates the battery feed:

```
                       ┌──────────────────────────────┐
   USB-C ── #4410 ─────┤  LiPo 3.7V 2000mAh (#2011)    │
           (charge)    └───────────────┬──────────────┘
                                       │  raw cell 3.0–4.2 V
                                 [EG1218 power switch]   (item 023)
                                       │
                 ┌─────────────────────┴─────────────────────┐
                 │                                            │
        PowerBoost 500 (#1903)                     Pololu S7V8F3 buck-boost
        LiPo → regulated 5 V                       LiPo → regulated 3.3 V
        (item 021)                                 (item 022)
                 │                                            │
              5 V rail                                    3.3 V rail
                 │                                            │
              LM386 V+                     MSP430 + OLED + SRAM + Flash + 74HC165
        (≥4 V satisfied ✓)                 (≤3.6 V satisfied ✓, full-cell safe)
```

Why these parts:

- **5 V boost for audio.** The LM386 is the only part needing >3.3 V. Adafruit
  PowerBoost 500 gives a clean 5 V from the LiPo — comfortably inside the amp's
  4–12 V range — and has an EN pin the power switch can drive.
- **3.3 V buck-boost for logic.** A *buck-boost* (not a plain LDO) holds 3.3 V across
  the entire cell range (4.2 V down to ~3.0 V), so it both protects the MCU from the
  4.2 V full-charge peak and keeps logic alive as the battery drains — best runtime.
- **Master power switch.** A handheld needs an on/off control; none existed. A single
  SPDT slide switch in the LiPo feed (or on the PowerBoost EN pin) does it.

Simpler alternative (if minimizing modules): keep the PowerBoost for 5 V and derive
3.3 V with an LDO (e.g. MCP1700-3302E) fed **from the 5 V rail** — but the buck-boost
gives better efficiency and battery utilization for a portable device.

### Bench note

For breadboard bring-up over USB, the LaunchPad's on-board LDO already provides 3.3 V,
so items 021–023 are only strictly needed for **portable** operation and the **audio**
stage. Bring up logic/display/memory/input on USB first; add the power stage (Phase 5)
when going portable — and note the LM386 needs items 021 even on the bench.

---

## Compatible — no action needed

| Subsystem | Verdict |
|-----------|---------|
| OLED #2674 (SSD1325) | 3.3 V, on-board level shifter — fully compatible |
| 23LC1024 SRAM | 2.5–5.5 V, SPI — fine at 3.3 V |
| W25Q128 Flash (#5634) | 2.7–3.6 V, SPI — fine at 3.3 V |
| SN74HC165 shift register | HC family runs at 3.3 V; button levels rail-to-rail |
| Per-IC 0.1 µF decoupling | Present for MCU, SRAM, Flash, shift reg |
| Shared USCI_B0 SPI bus | Sound — separate CS per device |

---

## BOM changes applied (Rev F)

**Added:** 021 PowerBoost 500 Basic (5 V boost) · 022 Pololu S7V8F3 (3.3 V
buck-boost) · 023 E-Switch EG1218 (master power switch). New total **$138.05**
(was $116.55).

**Corrected:** item 010 #4410 relabeled "charge only — raw cell output, not
regulated"; LM386 note now specifies the 5 V rail; item 002 display relabeled
"monochrome" (Adafruit lists #2674 as monochrome, not grayscale); SPI-allocation
table W25Q32 → W25Q128; structured-BOM header "Rev C" → "Rev F".

---

## Secondary — internal doc drift (not BOM parts)

These are consistency issues across the schematic/wiring docs, flagged for a future
schematic/firmware pass — no BOM part change:

- **74HC165 SH/LD latch pin:** P2.5 (authoritative, schematic + generator + breadboard
  guide) vs P2.3 in `wiring/phase-3-buttons-shift-register.md` and P2.4 in old notes.
- **Audio PWM pin:** P1.2 (schematic + breadboard guide) vs P2.4 in
  `wiring/phase-4-audio.md`.
- **LM386 output coupling cap:** 220 µF (BOM) vs 250 µF (phase-4 wiring).
- **Volume pot (item 020):** in the BOM but not instantiated in the schematic.
- **Charger in schematic vs BOM:** the schematic models a discrete TP4056 + DW01A +
  AO3400 charger (anticipating a custom PCB), whereas the BOM uses the Adafruit #4410
  module. With items 021/022 added, the BOM's power stage and the schematic now agree
  in intent (charge + regulate) even though the exact parts differ.

---

## Sources

- Adafruit #4410 — Micro-Lipo Charger for LiPoly Batt with USB Type-C Jack:
  https://www.adafruit.com/product/4410
- Adafruit #2674 — Monochrome 2.7" 128×64 OLED Graphic Display (SSD1325):
  https://www.adafruit.com/product/2674
- TI LM386 datasheet (LM386N-1 supply range 4–12 V):
  https://www.ti.com/lit/ds/symlink/lm386.pdf
- Adafruit PowerBoost 500 Basic (#1903): https://www.adafruit.com/product/1903
- Pololu S7V8F3 3.3 V step-up/step-down regulator: https://www.pololu.com/product/2122
- MSP430G2553 datasheet (SLAS735) — recommended/abs-max VCC.

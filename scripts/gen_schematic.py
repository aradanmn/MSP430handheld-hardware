#!/usr/bin/env python3
"""
gen_schematic.py -- KiCad 9 schematic for the handheld carrier board (rev 6).

The parts and nets are NOT defined here: they come from pcb/handheld_design.py,
the same table the PCB is generated from, so the schematic and the board cannot
drift. This script only chooses symbols and draws.

Run inside the KiCad container (needs the stock symbol libraries):
    pcb/kicad.sh python3 scripts/gen_schematic.py schematic/msp430_handheld.kicad_sch

Every connected pin gets a short stub and a global label (or a power symbol for
GND / +3V3 / +5V); unconnected pins get a no-connect flag. scripts/check_netlist.py
then proves the result matches the PCB pin for pin.
"""
import math, os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "pcb"))
import handheld_design as D
from sexpr import Q, parse, dump, find

SYMDIR = "/usr/share/kicad/symbols/"
G = 2.54
POWER_SYMBOLS = {"GND": "power:GND", "+3V3": "power:+3V3", "+5V": "power:+5V"}
ROOT = str(uuid.uuid4())
uid = lambda: str(uuid.uuid4())

# ── 1. symbol choice (by reference prefix / exact reference) ────────────────
LIB = {
    "U1": "MCU_Texas_MSP430:MSP430G2553IN20", "U2": "74xx:74HC165", "U4": "Memory_Flash:W25Q128JVS",
    "U5": "Amplifier_Audio:LM386", "D1": "Device:LED", "RV1": "Device:R_Potentiometer",
    "SW9": "Switch:SW_SPDT", "J1": "Connector_Generic:Conn_01x02", "J2": "Connector_Generic:Conn_01x02",
    "J3": "Connector_Generic:Conn_01x06",
    "R": "Device:R", "C": "Device:C", "CP": "Device:C_Polarized", "SW": "Switch:SW_Push",
}
POLARISED = {"C7", "C8", "C9", "C11", "C13"}
HORIZONTAL = ("R", "C")            # two-pin passives are drawn lying down (rotation 90)

# Parts with no stock symbol: (pin number, name, electrical type), drawn as a box.
BOX = {
    "U3": ("23LC1024", [("1", "~{CS}", "input"), ("6", "SCK", "input"), ("5", "SI", "input"), ("2", "SO", "tri_state"),
                        ("3", "SIO2", "passive"), ("7", "~{HOLD}", "input"), ("8", "VCC", "power_in"), ("4", "VSS", "power_in")]),
    "A1": ("OLED_Adafruit_2674", [(str(i + 1), n or "NC", t) for i, (n, t) in enumerate(
        [("GND", "power_in"), ("3V3", "power_in"), ("", "passive"), ("DC", "input"), ("WR", "passive"), ("RD", "passive"),
         ("D0/CLK", "input"), ("D1/DIN", "input")] + [(f"D{i}", "passive") for i in range(2, 8)] +
        [("CS", "input"), ("RST", "input"), ("", "passive"), ("", "passive"), ("", "passive"), ("FG", "passive")])]),
    "A2": ("Charger_Adafruit_4410", [("1", "5V_USB", "passive"), ("2", "D-", "passive"), ("3", "D+", "passive"),
                                     ("4", "GND", "power_in"), ("5", "BAT", "power_out")]),
    "A3": ("PowerBoost_1903", [("1", "BAT", "power_in"), ("2", "GND", "power_in"), ("3", "EN", "input"),
                                           ("4", "LBO", "open_collector"), ("5", "GND", "power_in"), ("6", "5V", "power_out")]),
    "A4": ("Pololu_S7V8F3", [("1", "SHDN", "input"), ("2", "VIN", "power_in"), ("3", "GND", "power_in"), ("4", "VOUT", "power_out")]),
}

BLOCKS = [   # (title, refs in drawing order)
    ("MCU + PROGRAMMING", ["U1", "C1", "R12", "C2", "J3", "D1", "R17"]),
    ("DISPLAY", ["A1", "R9", "C13"]),
    ("MEMORY", ["U3", "C4", "R10", "U4", "C5", "R11"]),
    ("INPUT", ["U2", "C3", "R13"] + [x for i in range(1, 9) for x in (f"SW{i}", f"R{i}")]),
    ("AUDIO", ["R14", "C6", "C7", "RV1", "U5", "C10", "C11", "C8", "C9", "C12", "R16", "R15", "J2"]),
    ("POWER", ["J1", "A2", "SW9", "A3", "A4", "R18", "R19", "C14"]),
]


def lib_id_for(ref):
    if ref in BOX:
        return "handheld:" + BOX[ref][0]
    if ref in LIB:
        return LIB[ref]
    if ref in POLARISED:
        return LIB["CP"]
    return LIB[ref.rstrip("0123456789")]


# ── 2. symbol definitions for lib_symbols ───────────────────────────────────
_libcache = {}

def stock_symbol(lib_id):
    """Extract a stock symbol, resolving (extends ...), ready to embed."""
    lib, name = lib_id.split(":")
    if lib not in _libcache:
        _libcache[lib] = {s[1]: s for s in find(parse(open(SYMDIR + lib + ".kicad_sym").read()), "symbol")}
    sym = _libcache[lib][name]
    ext = find(sym, "extends")
    if ext:
        parent = _libcache[lib][ext[0][1]]
        body = [c for c in parent if isinstance(c, list) and c[0] not in ("property", "embedded_fonts")]
        for sub in body:
            if sub[0] == "symbol":
                sub[1] = Q(sub[1].replace(parent[1], name, 1))
        props = find(sym, "property")
        have = {p[1] for p in props}
        props += [p for p in find(parent, "property") if p[1] not in have]
        sym = ["symbol", Q(name)] + [b for b in body if b[0] != "symbol"] + props + [b for b in body if b[0] == "symbol"]
    out = ["symbol", Q(lib_id)]
    for c in sym[2:]:
        if isinstance(c, list) and c[0] in ("embedded_fonts", "extends"):
            continue
        if isinstance(c, list) and c[0] == "property":
            c = [x for x in c if not (isinstance(x, list) and x[0] == "id")]
        out.append(c)
    return out


def box_symbol(name, pins):
    n = len(pins)
    top = (n - 1) * G / 2
    half_w = 10.16
    eff = '(effects (font (size 1.27 1.27)))'
    s = [f'(symbol "handheld:{name}" (exclude_from_sim no) (in_bom yes) (on_board yes)',
         f'(property "Reference" "U" (at {-half_w} {top + 3.81} 0) (effects (font (size 1.27 1.27)) (justify left)))',
         f'(property "Value" "{name}" (at {-half_w} {-top - 3.81} 0) (effects (font (size 1.27 1.27)) (justify left)))',
         '(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         '(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         f'(symbol "{name}_0_1" (rectangle (start {-half_w} {top + G}) (end {half_w} {-top - G})'
         ' (stroke (width 0.254) (type default)) (fill (type background))))',
         f'(symbol "{name}_1_1"']
    for i, (num, pname, ptype) in enumerate(pins):
        s.append(f'(pin {ptype} line (at {-half_w - G} {top - i * G} 0) (length {G})'
                 f' (name "{pname}" {eff}) (number "{num}" {eff}))')
    s.append("))")
    return parse(" ".join(s))


def pins_of(symdef):
    """[(number, name, x, y, angle, type)] for unit 1 (+ common unit 0) of a symbol definition."""
    out = []
    for sub in find(symdef, "symbol"):
        unit = sub[1].rsplit("_", 2)[1]
        if unit not in ("0", "1"):
            continue
        for p in find(sub, "pin"):
            at = find(p, "at")[0]
            out.append((find(p, "number")[0][1], find(p, "name")[0][1], float(at[1]), float(at[2]), int(float(at[3])), p[1]))
    return out


# ── 3. geometry ─────────────────────────────────────────────────────────────
def pin_world(cx, cy, rot, px, py, pangle):
    """Pin tip in sheet coordinates and the direction (dx, dy) a wire leaves it."""
    a = math.radians(rot)
    x = px * math.cos(a) - py * math.sin(a)
    y = px * math.sin(a) + py * math.cos(a)
    out = math.radians((pangle + rot + 180) % 360)          # pin angle points INTO the body
    return (cx + x, cy - y, round(math.cos(out)), -round(math.sin(out)))


def label_len(net):
    return 0 if net is None else (4.0 if net in POWER_SYMBOLS else 2 * G + 1.15 * len(net) + 3.0)


class Part:
    def __init__(self, ref, spec, value, padnets, symdef):
        self.ref, self.fp, self.value, self.nets, self.lib_id = ref, spec, value, padnets, symdef[1]
        self.rot = 90 if (ref.rstrip("0123456789") in HORIZONTAL) else 0
        self.pins = pins_of(symdef)
        nums = {p[0] for p in self.pins}
        missing = set(padnets) - nums
        assert not missing, f"{ref}: nets on pins {missing} that symbol {self.lib_id} does not have"
        # extents around the centre, including labels
        ext = [0, 0, 0, 0]                                   # left, top, right, bottom
        for num, _, px, py, pa, _ in self.pins:
            x, y, dx, dy = pin_world(0, 0, self.rot, px, py, pa)
            reach = label_len(self.nets.get(num))
            ext[0] = min(ext[0], x + dx * reach if dx < 0 else x)
            ext[2] = max(ext[2], x + dx * reach if dx > 0 else x)
            ext[1] = min(ext[1], y + dy * reach if dy < 0 else y)
            ext[3] = max(ext[3], y + dy * reach if dy > 0 else y)
        ext[1] = min(ext[1], -3.0) - 4.0                     # room for the reference text
        ext[3] = max(ext[3], 3.0) + 4.0                      # ... and the value
        self.ext = ext


def snap(v):
    return round(v / G) * G


# ── 4. S-expression builders for placed items ───────────────────────────────
def wire(x1, y1, x2, y2):
    return f'(wire (pts (xy {x1:.4f} {y1:.4f}) (xy {x2:.4f} {y2:.4f})) (stroke (width 0) (type default)) (uuid "{uid()}"))'


def glabel(net, x, y, dx, dy):
    rot = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[(dx, dy)]
    just = "right" if rot in (180, 270) else "left"
    return (f'(global_label "{net}" (shape passive) (at {x:.4f} {y:.4f} {rot}) (fields_autoplaced yes)'
            f' (effects (font (size 1.27 1.27)) (justify {just})) (uuid "{uid()}"))')


_pwr = [0]

def power(lib_id, net, x, y, rot=0):
    _pwr[0] += 1
    return (f'(symbol (lib_id "{lib_id}") (at {x:.4f} {y:.4f} {rot}) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)'
            f' (uuid "{uid()}")'
            f' (property "Reference" "#PWR{_pwr[0]:03d}" (at {x:.4f} {y:.4f} 0) (effects (font (size 1.27 1.27)) (hide yes)))'
            f' (property "Value" "{net}" (at {x:.4f} {y + (3.6 if net == "GND" else -3.6):.4f} 0) (effects (font (size 1.0 1.0))))'
            f' (property "Footprint" "" (at {x:.4f} {y:.4f} 0) (effects (font (size 1.27 1.27)) (hide yes)))'
            f' (property "Datasheet" "" (at {x:.4f} {y:.4f} 0) (effects (font (size 1.27 1.27)) (hide yes)))'
            f' (pin "1" (uuid "{uid()}"))'
            f' (instances (project "msp430_handheld" (path "/{ROOT}" (reference "#PWR{_pwr[0]:03d}") (unit 1)))))')


def place(part, cx, cy):
    out = []
    e = part.ext
    fa = part.rot          # a field's angle is relative to its symbol: this keeps the text horizontal
    out.append(
        f'(symbol (lib_id "{part.lib_id}") (at {cx:.4f} {cy:.4f} {part.rot}) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)'
        f' (uuid "{uid()}")'
        f' (property "Reference" "{part.ref}" (at {cx + e[0] + 1:.4f} {cy + e[1] + 1.5:.4f} {fa}) (effects (font (size 1.27 1.27)) (justify left)))'
        f' (property "Value" "{part.value}" (at {cx + e[0] + 1:.4f} {cy + e[3] - 1.5:.4f} {fa}) (effects (font (size 1.27 1.27)) (justify left)))'
        f' (property "Footprint" "{part.fp}" (at {cx:.4f} {cy:.4f} 0) (effects (font (size 1.27 1.27)) (hide yes)))'
        f' (property "Datasheet" "" (at {cx:.4f} {cy:.4f} 0) (effects (font (size 1.27 1.27)) (hide yes)))'
        + "".join(f' (pin "{n}" (uuid "{uid()}"))' for n in sorted({p[0] for p in part.pins}))
        + f' (instances (project "msp430_handheld" (path "/{ROOT}" (reference "{part.ref}") (unit 1)))))')
    for num, _, px, py, pa, _ in part.pins:
        x, y, dx, dy = pin_world(cx, cy, part.rot, px, py, pa)
        net = part.nets.get(num)
        if net is None:
            out.append(f'(no_connect (at {x:.4f} {y:.4f}) (uuid "{uid()}"))')
            continue
        x2, y2 = x + dx * G, y + dy * G
        out.append(wire(x, y, x2, y2))
        if net in POWER_SYMBOLS:
            # GND points down, rails point up; turn the symbol to follow a sideways stub
            rot = {(0, 1): 0, (1, 0): 90, (0, -1): 180, (-1, 0): 270}[(dx, dy)] if net == "GND" else \
                  {(0, -1): 0, (-1, 0): 90, (0, 1): 180, (1, 0): 270}[(dx, dy)]
            out.append(power(POWER_SYMBOLS[net], net, x2, y2, rot))
        else:
            out.append(glabel(net, x2, y2, dx, dy))
    return out


def text(s, x, y, size=3.0):
    return (f'(text "{s}" (exclude_from_sim no) (at {x:.4f} {y:.4f} 0)'
            f' (effects (font (size {size} {size}) (thickness {size * 0.15:.3f})) (justify left bottom)) (uuid "{uid()}"))')


# ── 5. page builder ─────────────────────────────────────────────────────────
PAPER = {"A3": (420.0, 297.0), "A2": (594.0, 420.0), "A1": (841.0, 594.0)}


def layout(parts, page_w, page_h):
    """Flow each block top-to-bottom into as many sub-columns as it needs; None if the page is too small."""
    margin, top, bottom, gap = 15.0, 28.0, page_h - 40.0, 6.0
    x = margin
    items, titles = [], []
    for title, refs in BLOCKS:
        titles.append((title, x, top - 6))
        col_x, y, col_w = x, top, 0.0
        for ref in refs:
            p = parts[ref]
            h = p.ext[3] - p.ext[1]
            if y + h > bottom and y > top:
                col_x += col_w + gap; y = top; col_w = 0.0
            cx, cy = snap(col_x - p.ext[0] + G), snap(y - p.ext[1] + G)
            items.append((p, cx, cy))
            y = cy + p.ext[3] + 2.0
            col_w = max(col_w, (cx + p.ext[2]) - col_x)
        x = col_x + col_w + 14.0
    return (items, titles) if x - 14.0 <= page_w - margin else None


def build():
    design = {p[0]: p for p in D.PARTS}
    assert sorted(design) == sorted(r for _, refs in BLOCKS for r in refs), "BLOCKS must list every part exactly once"
    symdefs = {}
    parts = {}
    for ref, (_, spec, value, *_rest, padnets) in design.items():
        lid = lib_id_for(ref)
        if lid not in symdefs:
            symdefs[lid] = box_symbol(*BOX[ref]) if ref in BOX else stock_symbol(lid)
        parts[ref] = Part(ref, spec, value, padnets, symdefs[lid])
    for lid in list(POWER_SYMBOLS.values()) + ["power:PWR_FLAG"]:
        symdefs[lid] = stock_symbol(lid)

    for paper, (pw, ph) in PAPER.items():
        placed = layout(parts, pw, ph)
        if placed:
            break
    else:
        raise SystemExit("design does not fit on A1")
    items, titles = placed

    body = []
    for title, x, y in titles:
        body.append(text(title, x, y))
    for p, cx, cy in items:
        body += place(p, cx, cy)
    # GND has no power-output pin anywhere (it comes in on the battery lead): flag it as driven.
    fx, fy = pw - 40.0, ph - 60.0
    fx, fy = snap(fx), snap(fy)
    body.append(power("power:PWR_FLAG", "PWR_FLAG", fx, fy))
    body.append(wire(fx, fy, fx, fy + G))
    body.append(power("power:GND", "GND", fx, fy + G))
    notes = [
        "Generated by scripts/gen_schematic.py from pcb/handheld_design.py - do not hand-edit.",
        "Pin map follows the firmware course: P2.3 SR_LOAD, P2.4 AUDIO_PWM (TA1.2), P2.5 SRAM_CS, P2.6 FLASH_CS.",
        "J3 carries Spy-Bi-Wire (RST, TEST) and the UART to a LaunchPad eZ-FET; same signal order as its J101 block.",
        "R13 isolates the 74HC165's always-driven QH from the shared MISO line. R9-R11 hold the chip selects high during reset.",
        "SW9 grounds PWR_EN (PowerBoost EN + Pololu SHDN) to switch off; it carries no load current.",
    ]
    for i, n in enumerate(notes):
        body.append(text(n, 15.0, ph - 32.0 + i * 4.0, 1.8))

    head = (f'(kicad_sch (version 20250114) (generator "gen_schematic") (generator_version "6.0") (uuid "{ROOT}")\n'
            f'  (paper "{paper}")\n'
            f'  (title_block (title "MSP430G2553 Handheld - carrier board") (date "{D.SCH_DATE}") (rev "6.0")\n'
            f'    (comment 1 "MSP430G2553IN20 on board; LaunchPad eZ-FET programs it over Spy-Bi-Wire (J3)")\n'
            f'    (comment 2 "SPI: P1.5 SCK, P1.6 MISO, P1.7 MOSI. CS: P2.0 OLED, P2.5 SRAM, P2.6 FLASH"))\n')
    libs = "  (lib_symbols\n" + "\n".join("    " + dump(s, 2) for s in symdefs.values()) + "\n  )\n"
    out = head + libs + "\n".join("  " + b for b in body) + '\n  (sheet_instances (path "/" (page "1")))\n  (embedded_fonts no)\n)\n'
    assert out.count("(") == out.count(")"), "unbalanced parentheses"
    return out, paper, len(items)


if __name__ == "__main__":
    out, paper, n = build()
    open(sys.argv[1], "w").write(out)
    print(f"{n} parts on {paper} -> {sys.argv[1]}")

#!/usr/bin/env python3
# gen_handheld_hier.py — Framework-style hierarchical schematic set for the
# MSP430G2553 handheld. Generated fresh from the BOM; do not patch — regenerate.
#
# Produces (in ../schematic/handheld/):
#   msp430_handheld.kicad_sch   root "Block Diagram / Interfaces" sheet
#   sheet_mcu.kicad_sch         MSP430G2553 + decoupling
#   sheet_display.kicad_sch     Adafruit #2674 SSD1325 OLED module
#   sheet_memory.kicad_sch      23LC1024 SRAM + W25Q128 Flash
#   sheet_input.kicad_sch       74HC165 + 8 buttons + pull-ups
#   sheet_audio.kicad_sch       LM386 + RC filter + pot + speaker
#   sheet_power.kicad_sch       charger + 5V boost + 3V3 buck-boost + battery + switch
#   msp430_handheld.kicad_pro   minimal project file
#
# Symbols are HARVESTED from the committed component-level schematic
# (../schematic/msp430_gameboy.kicad_sch) because this host has no KiCad
# libraries installed. That file's lib_symbols are already validated to load
# in KiCad 9, so re-embedding them is safe.
#
# Connectivity model: every signal pin gets a short stub + a GLOBAL label.
# Global labels connect across all sheets of the hierarchy, so no fragile
# hierarchical sheet-pins are needed. Power pins get power symbols
# (+3V3 for logic, +5V for the LM386, GND common) — matching BOM Rev F.

import os, re, uuid, datetime

G = 2.54
HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, '..', 'schematic', 'msp430_gameboy.kicad_sch')
OUT  = os.path.join(HERE, '..', 'schematic', 'handheld')
PROJECT = 'msp430_handheld'

REV   = datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')
DATE  = datetime.datetime.utcnow().strftime('%Y-%m-%d')

def uid():
    return str(uuid.uuid4())

# ── Symbol harvesting ──────────────────────────────────────────────────────────
with open(SRC) as f:
    SRCTXT = f.read()

def harvest(libid):
    """Return the balanced-paren text of (symbol "libid" ...) from the source."""
    key = '(symbol "%s"' % libid
    i = SRCTXT.find(key)
    if i < 0:
        raise KeyError('symbol not found in source: ' + libid)
    depth = 0
    for j in range(i, len(SRCTXT)):
        c = SRCTXT[j]
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return SRCTXT[i:j + 1]
    raise ValueError('unbalanced symbol: ' + libid)

def parse_pins(block):
    """Parse pins from a symbol block. Returns (by_num, by_name).
    by_num[num] = (lx, ly, ang, name); by_name[name] = (lx, ly, ang, num)."""
    by_num, by_name = {}, {}
    for chunk in block.split('(pin ')[1:]:
        m_at   = re.search(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\)', chunk)
        m_name = re.search(r'\(name\s+"([^"]*)"', chunk)
        m_num  = re.search(r'\(number\s+"([^"]*)"', chunk)
        if not (m_at and m_num):
            continue
        lx, ly, ang = float(m_at.group(1)), float(m_at.group(2)), float(m_at.group(3))
        num = m_num.group(1)
        name = m_name.group(1) if m_name else ''
        by_num[num] = (lx, ly, ang, name)
        by_name[name] = (lx, ly, ang, num)
    return by_num, by_name

# Harvest the library symbols we reuse from the component-level schematic.
HARVEST_IDS = [
    'MCU_Texas_MSP430:MSP430G2553IN20',
    '74xx:74HC165',
    'Amplifier_Audio:LM386',
    'Memory_Flash:W25Q128JVS',
    'SRAM_23LC1024',
    'Device:R', 'Device:C', 'Device:LED', 'Device:Speaker',
    'Switch:SW_Push',
    'Connector:Conn_01x02_Pin',
    'power:VCC', 'power:GND',
]
SYM = {}          # lib_id -> block text
PINS = {}         # lib_id -> (by_num, by_name)
for lid in HARVEST_IDS:
    SYM[lid] = harvest(lid)
    PINS[lid] = parse_pins(SYM[lid])

# ── Power-rail clones (VCC -> +3V3, +5V, VBAT) ─────────────────────────────────
def clone_power(newname):
    t = SYM['power:VCC']
    t = t.replace('(symbol "power:VCC"', '(symbol "power:%s"' % newname)
    t = t.replace('"VCC_0_1"', '"%s_0_1"' % newname)
    t = t.replace('"VCC_1_1"', '"%s_1_1"' % newname)
    t = t.replace('(property "Value" "VCC"', '(property "Value" "%s"' % newname)
    return t

for rail in ['+3V3', '+5V', 'VBAT']:
    lid = 'power:' + rail
    SYM[lid] = clone_power(rail)
    PINS[lid] = parse_pins(SYM[lid])

# ── Custom module / connector symbols (Framework-style functional blocks) ──────
def make_module(libid, refpref, left, right, value, wG=8):
    """Build a rectangular module symbol. left/right are lists of pin names
    (top to bottom). Pins are 'passive'. Returns block; registers pins."""
    bare = libid.split(':', 1)[1]
    n = max(len(left), len(right))
    hG = max(n + 1, 4)
    top = (hG / 2.0) * G
    halfw = (wG / 2.0) * G
    lines = []
    lines.append('\t\t(symbol "%s"' % libid)
    lines.append('\t\t\t(pin_names (offset 1.016))')
    lines.append('\t\t\t(exclude_from_sim no) (in_bom yes) (on_board yes)')
    lines.append('\t\t\t(property "Reference" "%s" (at 0 %.4f 0) (effects (font (size 1.27 1.27))))' % (refpref, top + G))
    lines.append('\t\t\t(property "Value" "%s" (at 0 %.4f 0) (effects (font (size 1.27 1.27))))' % (value, -top - G))
    lines.append('\t\t\t(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    lines.append('\t\t\t(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    lines.append('\t\t\t(symbol "%s_0_1"' % bare)
    lines.append('\t\t\t\t(rectangle (start %.4f %.4f) (end %.4f %.4f)' % (-halfw, top, halfw, -top))
    lines.append('\t\t\t\t\t(stroke (width 0.254) (type default)) (fill (type background)))')
    lines.append('\t\t\t)')
    lines.append('\t\t\t(symbol "%s_1_1"' % bare)
    pins = {}
    def emit_pin(name, num, lx, ly, ang):
        lines.append('\t\t\t\t(pin passive line (at %.4f %.4f %d) (length 5.08)' % (lx, ly, ang))
        lines.append('\t\t\t\t\t(name "%s" (effects (font (size 1.016 1.016))))' % name)
        lines.append('\t\t\t\t\t(number "%s" (effects (font (size 1.016 1.016)))))' % num)
        pins[num] = (lx, ly, float(ang), name)
    num = 1
    for k, name in enumerate(left):
        ly = top - (k + 1) * G
        emit_pin(name, str(num), -halfw - 5.08, ly, 0); num += 1
    for k, name in enumerate(right):
        ly = top - (k + 1) * G
        emit_pin(name, str(num), halfw + 5.08, ly, 180); num += 1
    lines.append('\t\t\t)')
    lines.append('\t\t)')
    block = '\n'.join(lines)
    by_num = pins
    by_name = {v[3]: (v[0], v[1], v[2], k) for k, v in pins.items()}
    SYM[libid] = block
    PINS[libid] = (by_num, by_name)
    return block

# Adafruit #2674 SSD1325 OLED module (breakout with on-board regulator/level shift)
make_module('Module:OLED_2674', 'DS',
            ['VIN', 'GND', 'SCK', 'MOSI'], ['CS', 'DC', 'RST'],
            'OLED_SSD1325_2674', wG=10)
# Adafruit #4410 USB-C Micro-Lipo charger (charge only)
make_module('Module:Charger_4410', 'U',
            ['USB_C'], ['BAT+', 'BAT-'], 'Charger_4410', wG=8)
# Adafruit #1903 PowerBoost 500 (LiPo -> regulated 5V)
make_module('Module:PowerBoost_1903', 'U',
            ['BAT', 'GND', 'EN'], ['5V', 'GND2'], 'PowerBoost500_1903', wG=8)
# Pololu S7V8F3 (LiPo -> regulated 3.3V)
make_module('Module:S7V8F3', 'U',
            ['VIN', 'GND', 'EN'], ['VOUT', 'GND2'], 'S7V8F3_3V3', wG=8)
# SPDT slide switch (master power)
make_module('Module:SW_SPDT', 'SW',
            ['COM'], ['NO', 'NC'], 'EG1218', wG=6)
# 10k audio-taper volume pot (3-terminal)
make_module('Module:POT_10k', 'RV',
            ['1'], ['3', '2'], '10k_log_PTV09A', wG=6)

# ── S-expression builders ──────────────────────────────────────────────────────
def title_block(title, mainfunc):
    return ('\t(paper "B")\n'
            '\t(title_block\n'
            '\t\t(title "%s")\n'
            '\t\t(date "%s")\n'
            '\t\t(rev "%s")\n'
            '\t\t(company "MSP430 Handheld — open hardware")\n'
            '\t\t(comment 1 "%s")\n'
            '\t)\n' % (title, DATE, REV, mainfunc))

def sym_instance(libid, cx, cy, ref, val, root, sheetuuid, extra_hidden=None):
    bnum, _ = PINS[libid]
    # bounding for text: use nominal
    out = []
    out.append('\t(symbol')
    out.append('\t\t(lib_id "%s") (at %.4f %.4f 0) (unit 1)' % (libid, cx, cy))
    out.append('\t\t(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)')
    out.append('\t\t(fields_autoplaced yes)')
    out.append('\t\t(uuid "%s")' % uid())
    out.append('\t\t(property "Reference" "%s" (at %.4f %.4f 0) (effects (font (size 1.016 1.016)) (justify left)))' % (ref, cx + 2.54, cy - 2.54))
    out.append('\t\t(property "Value" "%s" (at %.4f %.4f 0) (effects (font (size 1.016 1.016)) (justify left)))' % (val, cx + 2.54, cy + 2.54))
    out.append('\t\t(property "Footprint" "" (at %.4f %.4f 0) (effects (font (size 1.016 1.016)) (hide yes)))' % (cx, cy))
    out.append('\t\t(property "Datasheet" "" (at %.4f %.4f 0) (effects (font (size 1.016 1.016)) (hide yes)))' % (cx, cy))
    if extra_hidden:
        for k, v in extra_hidden.items():
            out.append('\t\t(property "%s" "%s" (at %.4f %.4f 0) (effects (font (size 1.016 1.016)) (hide yes)))' % (k, v, cx, cy))
    out.append('\t\t(instances (project "%s" (path "/%s/%s" (reference "%s") (unit 1))))' % (PROJECT, root, sheetuuid, ref))
    out.append('\t)')
    return '\n'.join(out)

_PWRN = [0]
def pwr_instance(rail, x, y, rot=0):
    _PWRN[0] += 1
    libid = 'power:' + rail
    ref = '#PWR%02d' % _PWRN[0]
    return ('\t(symbol\n'
            '\t\t(lib_id "%s") (at %.4f %.4f %d) (unit 1)\n'
            '\t\t(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)\n'
            '\t\t(uuid "%s")\n'
            '\t\t(property "Reference" "%s" (at %.4f %.4f 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
            '\t\t(property "Value" "%s" (at %.4f %.4f 0) (effects (font (size 1.27 1.27)) (hide yes))))'
            % (libid, x, y, rot, uid(), ref, x, y - 3.81, rail, x, y + 1.5))

def wire(x1, y1, x2, y2):
    return ('\t(wire (pts (xy %.4f %.4f) (xy %.4f %.4f)) (stroke (width 0) (type default)) (uuid "%s"))'
            % (x1, y1, x2, y2, uid()))

def glabel(net, x, y, rot, shape='bidirectional'):
    just = 'left' if rot in (0, 90) else 'right'
    return ('\t(global_label "%s" (shape %s) (at %.4f %.4f %d) (fields_autoplaced yes)\n'
            '\t\t(effects (font (size 1.016 1.016)) (justify %s))\n'
            '\t\t(uuid "%s"))' % (net, shape, x, y, rot, just, uid()))

def nolabel_nc(x, y):
    return '\t(no_connect (at %.4f %.4f) (uuid "%s"))' % (x, y, uid())

def text(s, x, y, size=1.27, rot=0, bold=False):
    b = ' (bold yes)' if bold else ''
    return ('\t(text "%s" (at %.4f %.4f %d)\n'
            '\t\t(effects (font (size %.3f %.3f)%s) (justify left))\n'
            '\t\t(uuid "%s"))' % (s, x, y, rot, size, size, b, uid()))

def rect(x1, y1, x2, y2):
    return ('\t(rectangle (start %.4f %.4f) (end %.4f %.4f)\n'
            '\t\t(stroke (width 0.254) (type default)) (fill (type none)) (uuid "%s"))'
            % (x1, y1, x2, y2, uid()))

def sheet_symbol(name, filename, x, y, wG, hG, root, page):
    w, h = wG * G, hG * G
    return ('\t(sheet (at %.4f %.4f) (size %.4f %.4f)\n'
            '\t\t(fields_autoplaced yes)\n'
            '\t\t(stroke (width 0.1524) (type solid))\n'
            '\t\t(fill (color 0 0 0 0.0000))\n'
            '\t\t(uuid "%s")\n'
            '\t\t(property "Sheetname" "%s" (at %.4f %.4f 0) (effects (font (size 1.27 1.27)) (justify left bottom)))\n'
            '\t\t(property "Sheetfile" "%s" (at %.4f %.4f 0) (effects (font (size 1.016 1.016)) (justify left top)))\n'
            '\t\t(instances (project "%s" (path "/%s" (page "%s")))))'
            % (x, y, w, h, sheet_uuids[name], name, x, y - 0.5, filename, x, y + h + 1.0, PROJECT, root, page))

# ── Pin transform + auto-connect helper ────────────────────────────────────────
def worldpin(cx, cy, lx, ly):
    return (cx + lx, cy - ly)

def stub_dir(ang):
    # local ang -> world unit vector (Y-down world). 0:right 180:left 90:up 270:down
    return {0: (1, 0), 180: (-1, 0), 90: (0, -1), 270: (0, 1)}[int(ang) % 360]

def resolve_pin(libid, key):
    """Return (lx, ly, ang, pin_number). The 4th element is ALWAYS the pin
    number so place()'s `handled` set (keyed by number) stays consistent with
    the default no-connect sweep."""
    bnum, bname = PINS[libid]
    if key.startswith('#'):                     # explicit pin number, e.g. '#5'
        num = key[1:]
        lx, ly, ang, _name = bnum[num]
        return (lx, ly, ang, num)
    if key in bname:                            # pin name, e.g. '~{CS}'
        lx, ly, ang, num = bname[key]
        return (lx, ly, ang, num)
    # token match (for MSP430 long names): find a name containing key as a field
    for name, v in bname.items():
        if re.search(r'(^|[/\s])' + re.escape(key) + r'($|[/\s])', name):
            lx, ly, ang, num = v
            return (lx, ly, ang, num)
    raise KeyError('pin %r not in %s' % (key, libid))

def place(body, libid, ref, val, xG, yG, netmap, root, sheetuuid, default='nc'):
    """Place a symbol and auto-connect each pin per netmap.
    netmap: {pin_key: ('lbl', net[, shape]) | ('pwr', rail) | ('nc',)}.
    Unlisted pins use `default`."""
    cx, cy = xG * G, yG * G
    body.append(sym_instance(libid, cx, cy, ref, val, root, sheetuuid))
    bnum, _ = PINS[libid]
    handled = set()
    def connect(lx, ly, ang, spec):
        tipx, tipy = worldpin(cx, cy, lx, ly)
        dx, dy = stub_dir(ang)
        ex, ey = tipx + dx * G, tipy + dy * G
        kind = spec[0]
        if kind == 'pwr':
            body.append(pwr_instance(spec[1], tipx, tipy))
        elif kind == 'nc':
            body.append(nolabel_nc(tipx, tipy))
        elif kind == 'lbl':
            net = spec[1]
            shape = spec[2] if len(spec) > 2 else 'bidirectional'
            body.append(wire(tipx, tipy, ex, ey))
            lrot = 0 if dx > 0 else (180 if dx < 0 else (90 if dy < 0 else 270))
            body.append(glabel(net, ex, ey, lrot, shape))
    for key, spec in netmap.items():
        lx, ly, ang, num = resolve_pin(libid, key)
        connect(lx, ly, ang, spec)
        handled.add(num)
    if default == 'nc':
        for num, (lx, ly, ang, name) in bnum.items():
            if num not in handled:
                tipx, tipy = worldpin(cx, cy, lx, ly)
                body.append(nolabel_nc(tipx, tipy))

# ── File assembler ─────────────────────────────────────────────────────────────
def used_symbols(libids):
    seen, order = set(), []
    for l in libids:
        if l not in seen:
            seen.add(l); order.append(l)
    return order

def build_file(title, mainfunc, libids, body, root, is_root=False, sheets_block=''):
    parts = []
    parts.append('(kicad_sch')
    parts.append('\t(version 20250114)')
    parts.append('\t(generator "python-script")')
    parts.append('\t(generator_version "1.0")')
    parts.append('\t(uuid "%s")' % root)
    parts.append(title_block(title, mainfunc).rstrip('\n'))
    # lib_symbols
    parts.append('\t(lib_symbols')
    for lid in used_symbols(libids):
        parts.append(SYM[lid])
    parts.append('\t)')
    if sheets_block:
        parts.append(sheets_block)
    parts.extend(body)
    parts.append('\t(sheet_instances (path "/" (page "1")))')
    parts.append('\t(embedded_fonts no)')
    parts.append(')')
    return '\n'.join(parts) + '\n'

def check_balance(txt, name):
    depth = 0; instr = False
    for c in txt:
        if c == '"':
            instr = not instr
        elif not instr:
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth < 0:
                    raise ValueError('%s: paren underflow' % name)
    if depth != 0:
        raise ValueError('%s: unbalanced parens depth=%d' % (name, depth))

# ── UUIDs for hierarchy ────────────────────────────────────────────────────────
ROOT = uid()
SHEETS = ['MCU', 'Display', 'Memory', 'Input', 'Audio', 'Power']
sheet_uuids = {s: uid() for s in SHEETS}
sheet_files = {
    'MCU': 'sheet_mcu.kicad_sch', 'Display': 'sheet_display.kicad_sch',
    'Memory': 'sheet_memory.kicad_sch', 'Input': 'sheet_input.kicad_sch',
    'Audio': 'sheet_audio.kicad_sch', 'Power': 'sheet_power.kicad_sch',
}

FILES = {}   # filename -> text

# ── Sheet: MCU ─────────────────────────────────────────────────────────────────
def build_mcu():
    root, su = ROOT, sheet_uuids['MCU']
    body, libs = [], []
    lid = 'MCU_Texas_MSP430:MSP430G2553IN20'
    libs += [lid, 'power:+3V3', 'power:GND', 'Device:C']
    netmap = {
        'DVCC': ('pwr', '+3V3'), 'DVSS': ('pwr', 'GND'),
        'P1.2': ('lbl', 'PWM_OUT', 'output'),
        'P1.5': ('lbl', 'SCK', 'output'),
        'P1.6': ('lbl', 'MISO', 'input'),
        'P1.7': ('lbl', 'MOSI', 'output'),
        'P2.0': ('lbl', 'OLED_CS', 'output'),
        'P2.1': ('lbl', 'OLED_DC', 'output'),
        'P2.2': ('lbl', 'OLED_RST', 'output'),
        'P2.3': ('lbl', 'SRAM_CS', 'output'),
        'P2.4': ('lbl', 'FLASH_CS', 'output'),
        'P2.5': ('lbl', 'SH_LD', 'output'),
    }
    place(body, lid, 'U1', 'MSP430G2553', 60, 45, netmap, root, su)
    # decoupling cap C1: +3V3 -> GND
    cx, cy = 95 * G, 45 * G
    body.append(sym_instance('Device:C', cx, cy, 'C1', '100nF 10% 0402 6.3V X5R', root, su))
    _, _, _, _ = 0, 0, 0, 0
    p1 = worldpin(cx, cy, *PINS['Device:C'][0]['1'][:2])
    p2 = worldpin(cx, cy, *PINS['Device:C'][0]['2'][:2])
    body.append(pwr_instance('+3V3', p1[0], p1[1]))
    body.append(pwr_instance('GND', p2[0], p2[1]))
    FILES[sheet_files['MCU']] = build_file(
        'MSP430 Handheld — MCU', 'Main Function: MCU & SPI bus master',
        libs, body, root)

# ── Sheet: Display ─────────────────────────────────────────────────────────────
def build_display():
    root, su = ROOT, sheet_uuids['Display']
    body, libs = [], ['Module:OLED_2674', 'power:+3V3', 'power:GND']
    netmap = {
        'VIN': ('pwr', '+3V3'), 'GND': ('pwr', 'GND'),
        'SCK': ('lbl', 'SCK', 'input'), 'MOSI': ('lbl', 'MOSI', 'input'),
        'CS': ('lbl', 'OLED_CS', 'input'), 'DC': ('lbl', 'OLED_DC', 'input'),
        'RST': ('lbl', 'OLED_RST', 'input'),
    }
    place(body, 'Module:OLED_2674', 'DS1', 'Adafruit #2674 SSD1325 OLED',
          50, 40, netmap, root, su, default='none')
    FILES[sheet_files['Display']] = build_file(
        'MSP430 Handheld — Display', 'Main Function: 2.7in SSD1325 OLED (SPI)',
        libs, body, root)

# ── Sheet: Memory ──────────────────────────────────────────────────────────────
def build_memory():
    root, su = ROOT, sheet_uuids['Memory']
    body = []
    libs = ['SRAM_23LC1024', 'Memory_Flash:W25Q128JVS', 'power:+3V3', 'power:GND', 'Device:C']
    # SRAM 23LC1024
    sram = {
        '~{CS}': ('lbl', 'SRAM_CS', 'input'), 'SO': ('lbl', 'MISO', 'output'),
        'SI': ('lbl', 'MOSI', 'input'), 'SCK': ('lbl', 'SCK', 'input'),
        '~{HOLD}': ('pwr', '+3V3'), 'VCC': ('pwr', '+3V3'), 'GND': ('pwr', 'GND'),
        'NC': ('nc',),
    }
    place(body, 'SRAM_23LC1024', 'U4', '23LC1024-I/P', 45, 35, sram, root, su)
    # Flash W25Q128 (key by number: 1 ~CS,2 DO,3 ~WP,4 GND,5 DI,6 CLK,7 ~HOLD,8 VCC)
    flash = {
        '#1': ('lbl', 'FLASH_CS', 'input'), '#2': ('lbl', 'MISO', 'output'),
        '#3': ('pwr', '+3V3'), '#4': ('pwr', 'GND'),
        '#5': ('lbl', 'MOSI', 'input'), '#6': ('lbl', 'SCK', 'input'),
        '#7': ('pwr', '+3V3'), '#8': ('pwr', '+3V3'),
    }
    place(body, 'Memory_Flash:W25Q128JVS', 'U5', 'W25Q128JVSSIQ', 85, 35, flash, root, su)
    for ref, xg in [('C3', 60), ('C4', 100)]:
        cx, cy = xg * G, 60 * G
        body.append(sym_instance('Device:C', cx, cy, ref, '100nF 10% 0402 6.3V X5R', root, su))
        p1 = worldpin(cx, cy, *PINS['Device:C'][0]['1'][:2])
        p2 = worldpin(cx, cy, *PINS['Device:C'][0]['2'][:2])
        body.append(pwr_instance('+3V3', p1[0], p1[1]))
        body.append(pwr_instance('GND', p2[0], p2[1]))
    FILES[sheet_files['Memory']] = build_file(
        'MSP430 Handheld — Memory', 'Main Function: SPI SRAM + NOR Flash',
        libs, body, root)

# ── Sheet: Input ───────────────────────────────────────────────────────────────
def build_input():
    root, su = ROOT, sheet_uuids['Input']
    body = []
    libs = ['74xx:74HC165', 'Switch:SW_Push', 'Device:R', 'power:+3V3', 'power:GND', 'Device:C']
    hc = {
        '~{PL}': ('lbl', 'SH_LD', 'input'), 'CP': ('lbl', 'SCK', 'input'),
        'Q7': ('lbl', 'MISO', 'output'), '~{Q7}': ('nc',),
        'DS': ('pwr', 'GND'), '~{CE}': ('pwr', 'GND'),
        'VCC': ('pwr', '+3V3'), 'GND': ('pwr', 'GND'),
        'D0': ('lbl', 'BTN_A', 'input'), 'D1': ('lbl', 'BTN_B', 'input'),
        'D2': ('lbl', 'BTN_C', 'input'), 'D3': ('lbl', 'BTN_D', 'input'),
        'D4': ('lbl', 'BTN_E', 'input'), 'D5': ('lbl', 'BTN_F', 'input'),
        'D6': ('lbl', 'BTN_G', 'input'), 'D7': ('lbl', 'BTN_H', 'input'),
    }
    place(body, '74xx:74HC165', 'U2', 'SN74HC165N', 70, 40, hc, root, su)
    # 8 buttons + 8 pull-ups down the left. Button: pin1->GND, pin2->BTN_x + pull-up->+3V3
    nets = ['BTN_A', 'BTN_B', 'BTN_C', 'BTN_D', 'BTN_E', 'BTN_F', 'BTN_G', 'BTN_H']
    for i, net in enumerate(nets):
        yg = 20 + i * 8
        swm = {'1': ('pwr', 'GND'), '2': ('lbl', net, 'output')}
        place(body, 'Switch:SW_Push', 'SW%d' % (i + 1), net, 20, yg, swm, root, su, default='none')
        # pull-up R: pin1 +3V3, pin2 net
        rx, ry = 32 * G, yg * G
        body.append(sym_instance('Device:R', rx, ry, 'R%d' % (i + 2), '10k 5% 0402 0.1W', root, su))
        rp1 = worldpin(rx, ry, *PINS['Device:R'][0]['1'][:2])
        rp2 = worldpin(rx, ry, *PINS['Device:R'][0]['2'][:2])
        body.append(pwr_instance('+3V3', rp1[0], rp1[1]))
        body.append(wire(rp2[0], rp2[1], rp2[0], rp2[1] + G))
        body.append(glabel(net, rp2[0], rp2[1] + G, 270, 'input'))
    # decoupling
    cx, cy = 88 * G, 60 * G
    body.append(sym_instance('Device:C', cx, cy, 'C2', '100nF 10% 0402 6.3V X5R', root, su))
    p1 = worldpin(cx, cy, *PINS['Device:C'][0]['1'][:2])
    p2 = worldpin(cx, cy, *PINS['Device:C'][0]['2'][:2])
    body.append(pwr_instance('+3V3', p1[0], p1[1]))
    body.append(pwr_instance('GND', p2[0], p2[1]))
    FILES[sheet_files['Input']] = build_file(
        'MSP430 Handheld — Input', 'Main Function: 74HC165 8-button PISO input',
        libs, body, root)

# ── Sheet: Audio ───────────────────────────────────────────────────────────────
def build_audio():
    root, su = ROOT, sheet_uuids['Audio']
    body = []
    libs = ['Amplifier_Audio:LM386', 'Device:R', 'Device:C', 'Device:Speaker',
            'Module:POT_10k', 'power:+5V', 'power:GND']
    # LM386: +input from RC filter (PWM), -input GND, V+ +5V, GND, OUT->coupling->spk
    lm = {
        '+': ('lbl', 'AUD_IN', 'input'), '-': ('pwr', 'GND'),
        'V+': ('pwr', '+5V'), 'GND': ('pwr', 'GND'),
        '#5': ('lbl', 'AUD_OUT', 'output'),
        '#1': ('nc',), '#8': ('nc',), 'BYPASS': ('nc',),
    }
    place(body, 'Amplifier_Audio:LM386', 'U3', 'LM386N-1', 80, 40, lm, root, su, default='none')
    # RC filter: PWM_OUT -> R1(1k) -> node -> C5(10u) -> GND ; node -> pot -> AUD_IN
    rx, ry = 45 * G, 40 * G
    body.append(sym_instance('Device:R', rx, ry, 'R1', '1k 5% 0402 0.1W', root, su))
    rp1 = worldpin(rx, ry, *PINS['Device:R'][0]['1'][:2])
    rp2 = worldpin(rx, ry, *PINS['Device:R'][0]['2'][:2])
    body.append(wire(rp1[0], rp1[1], rp1[0], rp1[1] - G))
    body.append(glabel('PWM_OUT', rp1[0], rp1[1] - G, 90, 'input'))
    body.append(wire(rp2[0], rp2[1], rp2[0], rp2[1] + G))
    body.append(glabel('AUD_RC', rp2[0], rp2[1] + G, 270, 'passive'))
    # C5 filter cap to GND
    cx, cy = 52 * G, 48 * G
    body.append(sym_instance('Device:C', cx, cy, 'C5', '10uF 20% 0805 16V', root, su))
    cp1 = worldpin(cx, cy, *PINS['Device:C'][0]['1'][:2])
    cp2 = worldpin(cx, cy, *PINS['Device:C'][0]['2'][:2])
    body.append(wire(cp1[0], cp1[1], cp1[0], cp1[1] - G))
    body.append(glabel('AUD_RC', cp1[0], cp1[1] - G, 90, 'passive'))
    body.append(pwr_instance('GND', cp2[0], cp2[1]))
    # Volume pot: 1 -> AUD_RC, wiper(2) -> AUD_IN, 3 -> GND
    potm = {'1': ('lbl', 'AUD_RC', 'passive'), '2': ('lbl', 'AUD_IN', 'output'), '3': ('pwr', 'GND')}
    place(body, 'Module:POT_10k', 'RV1', '10k log PTV09A', 62, 55, potm, root, su, default='none')
    # Output coupling C7 220uF: AUD_OUT -> node -> R_S(10R) -> speaker+
    cx, cy = 100 * G, 40 * G
    body.append(sym_instance('Device:C', cx, cy, 'C7', '220uF 20% D6.3 16V', root, su))
    o1 = worldpin(cx, cy, *PINS['Device:C'][0]['1'][:2])
    o2 = worldpin(cx, cy, *PINS['Device:C'][0]['2'][:2])
    body.append(wire(o1[0], o1[1], o1[0], o1[1] - G))
    body.append(glabel('AUD_OUT', o1[0], o1[1] - G, 90, 'passive'))
    body.append(wire(o2[0], o2[1], o2[0], o2[1] + G))
    body.append(glabel('SPK_P', o2[0], o2[1] + G, 270, 'passive'))
    # Speaker LS1
    spk = {'1': ('lbl', 'SPK_P', 'passive'), '2': ('pwr', 'GND')}
    place(body, 'Device:Speaker', 'LS1', 'SP-3605 8ohm 0.5W', 112, 45, spk, root, su, default='none')
    FILES[sheet_files['Audio']] = build_file(
        'MSP430 Handheld — Audio', 'Main Function: LM386 PWM audio (5V rail)',
        libs, body, root)

# ── Sheet: Power ───────────────────────────────────────────────────────────────
def build_power():
    root, su = ROOT, sheet_uuids['Power']
    body = []
    libs = ['Module:Charger_4410', 'Module:PowerBoost_1903', 'Module:S7V8F3',
            'Module:SW_SPDT', 'Connector:Conn_01x02_Pin',
            'power:+5V', 'power:+3V3', 'power:VBAT', 'power:GND']
    # Charger #4410: USB_C in ; BAT+/- to battery + VBAT rail
    chg = {'USB_C': ('lbl', 'USB_C_IN', 'input'), 'BAT+': ('lbl', 'VBAT', 'output'), 'BAT-': ('pwr', 'GND')}
    place(body, 'Module:Charger_4410', 'U6', 'Adafruit #4410 charger', 25, 25, chg, root, su, default='none')
    # Battery BT1 (Conn_01x02): pin1 VBAT, pin2 GND
    bat = {'#1': ('lbl', 'VBAT', 'passive'), '#2': ('pwr', 'GND')}
    place(body, 'Connector:Conn_01x02_Pin', 'BT1', 'LiPo 3.7V 2000mAh #2011', 25, 45, bat, root, su, default='none')
    # Master slide switch: COM<-VBAT, NO->SYS_SW
    sw = {'COM': ('lbl', 'VBAT', 'passive'), 'NO': ('lbl', 'SYS_SW', 'output'), 'NC': ('nc',)}
    place(body, 'Module:SW_SPDT', 'SW9', 'EG1218 power switch', 50, 35, sw, root, su, default='none')
    # PowerBoost 500 -> +5V
    pb = {'BAT': ('lbl', 'SYS_SW', 'input'), 'GND': ('pwr', 'GND'), 'EN': ('lbl', 'SYS_SW', 'input'),
          '5V': ('pwr', '+5V'), 'GND2': ('pwr', 'GND')}
    place(body, 'Module:PowerBoost_1903', 'U7', 'Adafruit #1903 PowerBoost 500', 80, 25, pb, root, su, default='none')
    # S7V8F3 -> +3V3
    bb = {'VIN': ('lbl', 'SYS_SW', 'input'), 'GND': ('pwr', 'GND'), 'EN': ('lbl', 'SYS_SW', 'input'),
          'VOUT': ('pwr', '+3V3'), 'GND2': ('pwr', 'GND')}
    place(body, 'Module:S7V8F3', 'U8', 'Pololu S7V8F3 3V3', 80, 50, bb, root, su, default='none')
    FILES[sheet_files['Power']] = build_file(
        'MSP430 Handheld — Power', 'Main Function: LiPo charge + 5V/3V3 rails',
        libs, body, root)

# ── Root: Block Diagram / Interfaces ───────────────────────────────────────────
def build_root():
    body = []
    # Title text
    body.append(text('Block Diagram', 150 * G, 8 * G, size=5.0, bold=True))
    body.append(text('MSP430G2553 Handheld — Interfaces', 150 * G, 13 * G, size=2.0))
    # Sheet boxes (MCU-centric)
    # positions in G: (xG, yG, wG, hG)
    layout = {
        'MCU':     (95, 55, 34, 20),
        'Display': (150, 40, 30, 14),
        'Memory':  (150, 62, 30, 14),
        'Input':   (40, 55, 30, 14),
        'Audio':   (150, 84, 30, 14),
        'Power':   (95, 90, 34, 14),
    }
    pages = {'MCU': '2', 'Display': '3', 'Memory': '4', 'Input': '5', 'Audio': '6', 'Power': '7'}
    sblocks = []
    for name, (xg, yg, wg, hg) in layout.items():
        sblocks.append(sheet_symbol(name, sheet_files[name], xg * G, yg * G, wg, hg, ROOT, pages[name]))
    # Bus annotation text between MCU and peripherals (Framework style)
    def bus(label, xg, yg):
        body.append(text(label, xg * G, yg * G, size=1.6, bold=True))
    bus('SPI USCI_B0  SCK P1.5 / MOSI P1.7 / MISO P1.6', 131, 47)
    bus('OLED_CS P2.0 / DC P2.1 / RST P2.2', 131, 51)
    bus('SRAM_CS P2.3 / FLASH_CS P2.4', 131, 69)
    bus('SH/LD P2.5  (74HC165 latch)', 72, 58)
    bus('SCK/MISO shared SPI', 72, 62)
    bus('PWM_OUT P1.2  ->  RC + LM386', 131, 91)
    bus('+3V3 logic / +5V audio / GND', 131, 97)
    # Connector-type legend (Framework-style) top-left
    lx, ly = 8, 40
    body.append(text('Legend', lx * G, (ly - 2) * G, size=2.0, bold=True))
    legend = [
        ('Functional block (hierarchical sheet)', ly),
        ('SPI bus shared on USCI_B0 (P1.5/6/7)', ly + 4),
        ('CS/control = dedicated GPIO', ly + 8),
        ('Power: +3V3 logic, +5V audio', ly + 12),
    ]
    for s, yy in legend:
        body.append(rect(lx * G, yy * G - 3, (lx + 1.5) * G, yy * G))
        body.append(text(s, (lx + 2.5) * G, yy * G, size=1.4))
    # Power-rail legend bottom-left
    px, py = 8, 78
    body.append(text('Power rails', px * G, (py - 2) * G, size=2.0, bold=True))
    for i, r in enumerate(['USB-C 5V (charge)', 'VBAT 3.0-4.2V (LiPo)',
                           '+5V boost (LM386)', '+3V3 buck-boost (logic)', 'GND']):
        body.append(text('- ' + r, px * G, (py + 2 + i * 4) * G, size=1.4))
    sheets_block = '\n'.join(sblocks)
    FILES['%s.kicad_sch' % PROJECT] = build_file(
        'MSP430G2553 Handheld — Block Diagram', 'Root / Interfaces',
        ['power:+3V3', 'power:+5V', 'power:GND', 'power:VBAT'], body, ROOT,
        is_root=True, sheets_block=sheets_block)

# ── Project file ───────────────────────────────────────────────────────────────
def build_pro():
    return ('{\n'
            '  "board": {},\n'
            '  "meta": {"filename": "%s.kicad_pro", "version": 1},\n'
            '  "schematic": {},\n'
            '  "sheets": [],\n'
            '  "text_variables": {}\n'
            '}\n' % PROJECT)

# ── Build all ──────────────────────────────────────────────────────────────────
build_mcu()
build_display()
build_memory()
build_input()
build_audio()
build_power()
build_root()

os.makedirs(OUT, exist_ok=True)
for fn, txt in FILES.items():
    check_balance(txt, fn)
    with open(os.path.join(OUT, fn), 'w') as f:
        f.write(txt)
    print('wrote', fn, '(%d bytes)' % len(txt))
with open(os.path.join(OUT, '%s.kicad_pro' % PROJECT), 'w') as f:
    f.write(build_pro())
print('wrote %s.kicad_pro' % PROJECT)
print('OK — all files paren-balanced. Rev', REV)

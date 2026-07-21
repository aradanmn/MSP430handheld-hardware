"""
gen_kicad7.py — MSP430G2553 Game Boy schematic generator
Target: KiCad 9.0 native format (version 20250114)

Uses KiCad's built-in libraries for: MSP430G2553, 74HC165, LM386, W25Q128JVS.
Generates custom symbols for: 23LC1024 SRAM, connectors, passives, power.

Layout: MSP430G2553 at CENTER. Peripherals radiate outward:
  - OLED connector, SRAM, Flash: above
  - 74HC165 shift register + buttons: left
  - LM386 audio amp + speaker: right
  - Bypass caps: near MCU

Grid rule: ALL positions are integer multiples of G = 2.54 mm.
Coordinate convention:
  Symbol local:    Y-up  (math convention, same as KiCad .kicad_sym files)
  Schematic world: Y-down (screen convention)
  Mapping: world = (cx + lx,  cy - ly)

Run: python3 docs/hardware/scripts/gen_kicad7.py
Output: docs/hardware/schematic/msp430_gameboy.kicad_sch
"""

import re, uuid as _uuid, pathlib, datetime

G = 2.54  # 1 grid unit = 100 mil = 2.54 mm

KICAD_SYM = pathlib.Path(
    '/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols')

_TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
_TODAY = datetime.date.today().isoformat()            # used in title_block date
OUT_PATH = pathlib.Path(__file__).resolve().parents[1] / \
    f'schematic/msp430_gameboy_{_TS}.kicad_sch'


def uid():
    return str(_uuid.uuid4())


# ── Coordinate helpers ─────────────────────────────────────────────────────────

def pw(cx, cy, lx, ly):
    """Convert local (Y-up) pin position to world (Y-down) coords."""
    return (round(cx + lx, 4), round(cy - ly, 4))


def pin_w(comp_pos, pdict, key):
    lx, ly = pdict[key]
    return pw(comp_pos[0], comp_pos[1], lx, ly)


# ── Element accumulators ───────────────────────────────────────────────────────

PLACED, WIRES, LABELS, POWERS, NC, JUNCTIONS = [], [], [], [], [], []
STUB = G          # stub wire length between pin and label anchor

# Schematic UUID — generated once, referenced by all placed symbol instances blocks
SCH_UUID = uid()


def _wire(x1, y1, x2, y2):
    return (f'(wire (pts (xy {x1:.4f} {y1:.4f}) (xy {x2:.4f} {y2:.4f}))'
            f' (stroke (width 0) (type default)) (uuid "{uid()}"))')


def jct(x, y):
    """Explicit T-junction — required wherever three or more wires meet."""
    JUNCTIONS.append(
        f'(junction (at {x:.4f} {y:.4f}) (diameter 0) (color 0 0 0 0) (uuid "{uid()}"))'
    )


def _label(net, x, y, rot=0, shape='bidirectional'):
    # Global labels (arrow-shaped flags) connect same-named nets anywhere on the sheet.
    # shape: input | output | bidirectional | tri_state | passive
    # Font 1.016mm (40mil) fits within 2.54mm pin pitch without overlapping
    justify = 'right' if rot == 180 else 'left'
    return (f'(global_label "{net}" (shape {shape}) (at {x:.4f} {y:.4f} {rot})'
            f' (fields_autoplaced yes)'
            f' (effects (font (size 1.016 1.016)) (justify {justify}))'
            f' (uuid "{uid()}"))')


def _pwr_placed(sym, x, y):
    off = -2.54 if sym == 'VCC' else 2.54
    return (f'(symbol (lib_id "power:{sym}") (at {x:.4f} {y:.4f} 0)'
            f' (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)'
            f' (uuid "{uid()}")'
            f' (property "Reference" "#PWR"'
            f'  (at {x:.4f} {y+off:.4f} 0) (effects (font (size 1.27 1.27)) (hide yes)))'
            f' (property "Value" "{sym}"'
            f'  (at {x:.4f} {y-off:.4f} 0) (effects (font (size 1.27 1.27)) (hide yes)))'
            f')')


def _sym_placed(lib_id, cx, cy, ref, val, rot=0):
    # Reference offset: above-left of center so it doesn't hide behind component
    # instances block: KiCad 9 canonical reference — without this the ref shows "?" in the editor
    return (f'(symbol (lib_id "{lib_id}") (at {cx:.4f} {cy:.4f} {rot})'
            f' (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)'
            f' (fields_autoplaced yes)'
            f' (uuid "{uid()}")'
            f' (property "Reference" "{ref}"'
            f'  (at {cx:.4f} {cy-3.81:.4f} 0) (effects (font (size 1.016 1.016)) (justify left)))'
            f' (property "Value" "{val}"'
            f'  (at {cx:.4f} {cy+2.54:.4f} 0) (effects (font (size 1.016 1.016)) (justify left)))'
            f' (instances (project "" (path "/{SCH_UUID}" (reference "{ref}") (unit 1))))'
            f')')


def lbl(net, px, py, rot=0, shape='bidirectional'):
    """Global label with stub wire at pin endpoint (px, py).
    rot: 0=right, 180=left, 90=up (stub goes up, label above), 270=down (stub goes down, label below).
    """
    dirs = {0: (STUB, 0), 180: (-STUB, 0), 90: (0, -STUB), 270: (0, STUB)}
    dx, dy = dirs.get(rot, (0, 0))
    WIRES.append(_wire(px, py, px + dx, py + dy))
    LABELS.append(_label(net, px + dx, py + dy, rot, shape))


def pwr(sym, px, py):
    POWERS.append(_pwr_placed(sym, px, py))


def nc(px, py):
    NC.append(f'(no_connect (at {px:.4f} {py:.4f}) (uuid "{uid()}"))')


def wire_bypass_cap(cap_pos, vcc_world, gnd_world):
    """Wire a bypass cap in parallel to an IC's VCC and GND pins.

    cap_pos:   (cx, cy) mm — center of already-placed Device:C
    vcc_world: (x, y)  mm — IC VCC pin world coordinate
    gnd_world: (x, y)  mm — IC GND pin world coordinate

    Draws L-shaped wires:
        IC VCC pin → [horizontal + vertical] → cap pin 1 (VCC top)
        IC GND pin → [horizontal + vertical] → cap pin 2 (GND bottom)
    The IC's VCC/GND power symbols (placed elsewhere) complete the net.
    """
    cx, cy = cap_pos
    pin1 = pw(cx, cy, cp['1'][0], cp['1'][1])   # cap VCC terminal (world)
    pin2 = pw(cx, cy, cp['2'][0], cp['2'][1])   # cap GND terminal (world)
    vx, vy = vcc_world
    gx, gy = gnd_world

    # VCC side: route from IC VCC pin to cap pin 1
    if abs(vx - pin1[0]) > 0.001:              # different X → L-shape
        WIRES.append(_wire(vx, vy, pin1[0], vy))
        WIRES.append(_wire(pin1[0], vy, pin1[0], pin1[1]))
    else:                                       # same X → straight wire
        WIRES.append(_wire(vx, vy, pin1[0], pin1[1]))

    # GND side: route from IC GND pin to cap pin 2
    if abs(gx - pin2[0]) > 0.001:
        WIRES.append(_wire(gx, gy, pin2[0], gy))
        WIRES.append(_wire(pin2[0], gy, pin2[0], pin2[1]))
    else:
        WIRES.append(_wire(gx, gy, pin2[0], pin2[1]))


def place(lib_id, cx, cy, ref, val, rot=0):
    PLACED.append(_sym_placed(lib_id, cx, cy, ref, val, rot))


# ── KiCad library symbol extractor ────────────────────────────────────────────

def extract_sym(lib_name, sym_name):
    """Extract symbol from .kicad_sym for embedding in schematic lib_symbols.

    Returns (lib_sym_text, pin_by_name, pin_by_num).
    - lib_sym_text: standalone symbol block ready to embed (no 'extends')
    - pin_by_name / pin_by_num: {str: (lx, ly)} in Y-up local convention

    KiCad does NOT support 'extends' inside a schematic's lib_symbols section.
    Symbols that use extends are resolved here: parent's body/pin sub-symbols are
    merged into the child to produce a fully standalone block.
    """
    lib_text = (KICAD_SYM / f'{lib_name}.kicad_sym').read_text()

    def find_block(name):
        target = f'\t(symbol "{name}"'
        idx = lib_text.find(target)
        if idx == -1:
            raise KeyError(f'"{name}" not found in {lib_name}.kicad_sym')
        depth = 0
        for i in range(idx, len(lib_text)):
            if lib_text[i] == '(':
                depth += 1
            elif lib_text[i] == ')':
                depth -= 1
                if depth == 0:
                    return lib_text[idx:i + 1]
        raise ValueError(f'Unclosed parens for "{name}"')

    def parse_pins(block):
        by_name, by_num = {}, {}
        for m in re.finditer(
            r'\(pin\s+\S+\s+\S+\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)\s+\d+\)'
            r'.*?\(name\s+"([^"]*)"\s.*?\(number\s+"([^"]*)"\s',
            block, re.DOTALL
        ):
            lx, ly = float(m.group(1)), float(m.group(2))
            name, num = m.group(3), m.group(4)
            if name:
                by_name[name] = (lx, ly)
            by_num[num] = (lx, ly)
        return by_name, by_num

    def get_properties(block):
        """Extract property/flag lines between outer header and first sub-symbol."""
        first_nl = block.index('\n')
        sub_idx  = block.find('\t\t(symbol "')
        content  = block[first_nl + 1 : sub_idx if sub_idx != -1 else block.rindex('\n')]
        # Strip extends and embedded_fonts — both invalid in schematic lib_symbols
        content  = re.sub(r'\t*\(extends\s+"[^"]+"\)\n?', '', content)
        content  = re.sub(r'\t*\(embedded_fonts\s+[^)]+\)\n?', '', content)
        return content

    def get_sub_syms(block, src_name):
        """Extract (symbol "SRC_NAME_N_M" ...) blocks."""
        blocks, pos = [], 0
        target = f'\t\t(symbol "{src_name}_'
        while True:
            idx = block.find(target, pos)
            if idx == -1:
                break
            depth = 0
            for i in range(idx, len(block)):
                if block[i] == '(':
                    depth += 1
                elif block[i] == ')':
                    depth -= 1
                    if depth == 0:
                        blocks.append(block[idx:i + 1])
                        pos = i + 1
                        break
        return blocks

    def make_standalone(name, props, sub_syms):
        """Assemble a standalone lib_symbols-ready block."""
        # Ensure mandatory KiCad 9 symbol attributes are present
        flags = ''
        if '(exclude_from_sim' not in props:
            flags += '\t\t(exclude_from_sim no)\n'
        if '(in_bom' not in props:
            flags += '\t\t(in_bom yes)\n'
        if '(on_board' not in props:
            flags += '\t\t(on_board yes)\n'
        subs = '\n'.join(sub_syms)
        return (
            f'\t(symbol "{lib_name}:{name}"\n'
            f'{flags}'
            f'{props}'
            f'{subs}\n'
            f'\t\t(embedded_fonts no)\n'
            f'\t)'
        )

    main_block = find_block(sym_name)
    ext_m      = re.search(r'\(extends\s+"([^"]+)"\)', main_block)

    if ext_m:
        parent_name  = ext_m.group(1)
        parent_block = find_block(parent_name)
        by_name, by_num = parse_pins(parent_block)

        # Merge: child's properties + parent's sub-symbols renamed to child
        props    = get_properties(main_block)
        subs_raw = get_sub_syms(parent_block, parent_name)
        subs     = [s.replace(f'"{parent_name}_', f'"{sym_name}_')
                    for s in subs_raw]
        sym_text = make_standalone(sym_name, props, subs)
    else:
        by_name, by_num = parse_pins(main_block)
        props    = get_properties(main_block)
        subs     = get_sub_syms(main_block, sym_name)
        sym_text = make_standalone(sym_name, props, subs)

    return sym_text, by_name, by_num


# ── Custom symbol helpers ──────────────────────────────────────────────────────

def _rect_sym(name, ref_prefix, pins_left, bw=3*G, extra_pins=''):
    """Build a rectangular IC symbol with left-side signal pins.
    pins_left: list of (pin_name, ly_units, pin_num_str, pin_type)
    Returns (sym_text, pin_by_name, pin_by_num).
    """
    PX = bw + G
    BH = (len(pins_left) / 2 + 0.5) * G
    pins_str = ''
    by_name, by_num = {}, {}
    for pname, ly, pnum, ptype in pins_left:
        pins_str += (
            f'      (pin {ptype} line (at {-PX:.4f} {ly:.4f} 0) (length {G:.4f})\n'
            f'        (name "{pname}" (effects (font (size 1.016 1.016))))\n'
            f'        (number "{pnum}" (effects (font (size 1.016 1.016)))))\n'
        )
        key = re.sub(r'[~{{}}]', '', pname)
        by_name[key] = (-PX, ly)
        by_num[pnum]  = (-PX, ly)
    sym_text = (
        f'  (symbol "{name}"\n'
        f'    (in_bom yes) (on_board yes)\n'
        f'    (property "Reference" "{ref_prefix}" (at 0 {BH+2:.4f} 0)\n'
        f'      (effects (font (size 1.27 1.27))))\n'
        f'    (property "Value" "{name}" (at 0 {-(BH+2):.4f} 0)\n'
        f'      (effects (font (size 1.27 1.27))))\n'
        f'    (symbol "{name}_0_1"\n'
        f'      (rectangle (start {-bw:.4f} {BH:.4f}) (end {bw:.4f} {-BH:.4f})\n'
        f'        (stroke (width 0.254) (type default)) (fill (type background))))\n'
        f'    (symbol "{name}_1_1"\n'
        f'{pins_str}'
        f'{extra_pins}'
        f'  ))'
    )
    return sym_text, by_name, by_num


def make_sram_sym():
    """23LC1024-I/P: SPI SRAM, 8-pin DIP. Signals on left, VCC/GND top/bottom."""
    BW, BH = 3*G, 4*G
    PX = BW + G
    pins = [
        ('~{CS}',   3*G,  '1', 'input'),
        ('SO',      2*G,  '2', 'output'),
        ('NC',      1*G,  '3', 'no_connect'),
        ('SI',     -1*G,  '5', 'input'),
        ('SCK',    -2*G,  '6', 'input'),
        ('~{HOLD}',-3*G,  '7', 'input'),
    ]
    by_name, by_num = {}, {}
    pins_str = ''
    for pname, ly, pnum, ptype in pins:
        pins_str += (
            f'      (pin {ptype} line (at {-PX:.4f} {ly:.4f} 0) (length {G:.4f})\n'
            f'        (name "{pname}" (effects (font (size 1.016 1.016))))\n'
            f'        (number "{pnum}" (effects (font (size 1.016 1.016)))))\n'
        )
        key = re.sub(r'[~{}]', '', pname)
        by_name[key] = (-PX, ly)
        by_num[pnum]  = (-PX, ly)
    # VCC top, GND bottom
    pins_str += (
        f'      (pin power_in line (at 0 {BH+G:.4f} 270) (length {G:.4f})\n'
        f'        (name "VCC" (effects (font (size 1.016 1.016))))\n'
        f'        (number "8" (effects (font (size 1.016 1.016)))))\n'
        f'      (pin power_in line (at 0 {-(BH+G):.4f} 90) (length {G:.4f})\n'
        f'        (name "GND" (effects (font (size 1.016 1.016))))\n'
        f'        (number "4" (effects (font (size 1.016 1.016)))))\n'
    )
    by_name['VCC'] = (0, BH+G)
    by_name['GND'] = (0, -(BH+G))
    by_num['8'] = (0, BH+G)
    by_num['4'] = (0, -(BH+G))
    sym_text = (
        f'  (symbol "SRAM_23LC1024"\n'
        f'    (in_bom yes) (on_board yes)\n'
        f'    (property "Reference" "U" (at 0 {BH+3:.4f} 0)\n'
        f'      (effects (font (size 1.27 1.27))))\n'
        f'    (property "Value" "SRAM_23LC1024" (at 0 {-(BH+3):.4f} 0)\n'
        f'      (effects (font (size 1.27 1.27))))\n'
        f'    (symbol "SRAM_23LC1024_0_1"\n'
        f'      (rectangle (start {-BW:.4f} {BH:.4f}) (end {BW:.4f} {-BH:.4f})\n'
        f'        (stroke (width 0.254) (type default)) (fill (type background))))\n'
        f'    (symbol "SRAM_23LC1024_1_1"\n'
        f'{pins_str}'
        f'  ))'
    )
    return sym_text, by_name, by_num


def make_conn_sym(sym_name, pin_names, bw=G):
    """Single-row connector with all pins on left side."""
    n = len(pin_names)
    PX = bw + G
    BH = (n / 2) * G
    pins_str = ''
    by_name, by_num = {}, {}
    for i, pname in enumerate(pin_names):
        ly = (n / 2 - 0.5 - i) * G
        pnum = str(i + 1)
        pins_str += (
            f'      (pin passive line (at {-PX:.4f} {ly:.4f} 0) (length {G:.4f})\n'
            f'        (name "{pname}" (effects (font (size 1.016 1.016))))\n'
            f'        (number "{pnum}" (effects (font (size 1.016 1.016)))))\n'
        )
        by_name[pname] = (-PX, ly)
        by_num[pnum]   = (-PX, ly)
    sym_text = (
        f'  (symbol "{sym_name}"\n'
        f'    (in_bom yes) (on_board yes)\n'
        f'    (property "Reference" "J" (at 0 {BH+2:.4f} 0)\n'
        f'      (effects (font (size 1.27 1.27))))\n'
        f'    (property "Value" "{sym_name}" (at 0 {-(BH+2):.4f} 0)\n'
        f'      (effects (font (size 1.27 1.27))))\n'
        f'    (symbol "{sym_name}_0_1"\n'
        f'      (rectangle (start {-bw:.4f} {BH:.4f}) (end {bw:.4f} {-BH:.4f})\n'
        f'        (stroke (width 0.254) (type default)) (fill (type background))))\n'
        f'    (symbol "{sym_name}_1_1"\n'
        f'{pins_str}'
        f'  ))'
    )
    return sym_text, by_name, by_num


def make_passive_sym(name, ref, L=3.81, style='R'):
    """Vertical 2-pin passive (R or C). L=pin endpoint offset from center."""
    BH = 2.032 if style == 'R' else 0.508
    if style == 'R':
        body = (f'      (rectangle (start {-G:.4f} {BH:.4f}) (end {G:.4f} {-BH:.4f})\n'
                f'        (stroke (width 0.254) (type default)) (fill (type background)))\n')
    else:
        body = (f'      (polyline (pts (xy {-G:.4f} {BH:.4f}) (xy {G:.4f} {BH:.4f}))\n'
                f'        (stroke (width 0.508) (type default)) (fill (type none)))\n'
                f'      (polyline (pts (xy {-G:.4f} {-BH:.4f}) (xy {G:.4f} {-BH:.4f}))\n'
                f'        (stroke (width 0.508) (type default)) (fill (type none)))\n')
    pin_len = L - BH
    sym_text = (
        f'  (symbol "{name}"\n'
        f'    (in_bom yes) (on_board yes)\n'
        f'    (property "Reference" "{ref}" (at {G:.4f} 0 90)\n'
        f'      (effects (font (size 1.27 1.27))))\n'
        f'    (property "Value" "{name}" (at {-G:.4f} 0 90)\n'
        f'      (effects (font (size 1.27 1.27))))\n'
        f'    (symbol "{name}_0_1"\n{body}    )\n'
        f'    (symbol "{name}_1_1"\n'
        f'      (pin passive line (at 0 {L:.4f} 270) (length {pin_len:.4f})\n'
        f'        (name "~" (effects (font (size 1.27 1.27))))\n'
        f'        (number "1" (effects (font (size 1.27 1.27)))))\n'
        f'      (pin passive line (at 0 {-L:.4f} 90) (length {pin_len:.4f})\n'
        f'        (name "~" (effects (font (size 1.27 1.27))))\n'
        f'        (number "2" (effects (font (size 1.27 1.27)))))\n'
        f'  ))'
    )
    by_num = {'1': (0, L), '2': (0, -L)}
    return sym_text, by_num




def make_speaker_sym():
    L = 2 * G
    by_num = {'1': (-L, 0), '2': (L, 0)}
    sym_text = (
        f'  (symbol "Speaker"\n    (in_bom yes) (on_board yes)\n'
        f'    (property "Reference" "LS" (at 0 {2.5:.4f} 0)\n'
        f'      (effects (font (size 1.27 1.27))))\n'
        f'    (property "Value" "Speaker" (at 0 {-2.5:.4f} 0)\n'
        f'      (effects (font (size 1.27 1.27))))\n'
        f'    (symbol "Speaker_0_1"\n'
        f'      (polyline (pts (xy {-G:.4f} {G:.4f}) (xy {-G:.4f} {-G:.4f}))\n'
        '        (stroke (width 0.508) (type default)) (fill (type none)))\n'
        f'      (polyline (pts (xy {-G:.4f} {G:.4f}) (xy {G:.4f} {2*G:.4f})'
        f' (xy {G:.4f} {-2*G:.4f}) (xy {-G:.4f} {-G:.4f}))\n'
        '        (stroke (width 0.254) (type default)) (fill (type none))))\n'
        f'    (symbol "Speaker_1_1"\n'
        f'      (pin passive line (at {-L:.4f} 0 0) (length {G:.4f})\n'
        f'        (name "+" (effects (font (size 1.016 1.016))))\n'
        f'        (number "1" (effects (font (size 1.016 1.016)))))\n'
        f'      (pin passive line (at {L:.4f} 0 180) (length {G:.4f})\n'
        f'        (name "-" (effects (font (size 1.016 1.016))))\n'
        f'        (number "2" (effects (font (size 1.016 1.016)))))\n'
        f'  ))'
    )
    return sym_text, by_num


def make_sw_sym():
    """Horizontal push-button switch, 2-pin."""
    L = G
    by_num = {'1': (-L, 0), '2': (L, 0)}
    sym_text = (
        f'  (symbol "SW_Push"\n    (in_bom yes) (on_board yes)\n'
        f'    (property "Reference" "SW" (at 0 {2.5:.4f} 0)\n'
        f'      (effects (font (size 1.27 1.27))))\n'
        f'    (property "Value" "SW_Push" (at 0 {-2.5:.4f} 0)\n'
        f'      (effects (font (size 1.27 1.27))))\n'
        f'    (symbol "SW_Push_0_1"\n'
        f'      (polyline (pts (xy {-L:.4f} 0) (xy {-0.5*L:.4f} 0))'
        f' (stroke (width 0) (type default)) (fill (type none)))\n'
        f'      (polyline (pts (xy {0.5*L:.4f} 0) (xy {L:.4f} 0))'
        f' (stroke (width 0) (type default)) (fill (type none)))\n'
        f'      (polyline (pts (xy {-0.5*L:.4f} {-0.5*L:.4f}) (xy {0.5*L:.4f} {-0.5*L:.4f}))'
        f' (stroke (width 0.1) (type default)) (fill (type none)))\n'
        f'      (arc (start {-0.5*L:.4f} 0) (mid 0 {0.4*L:.4f}) (end {0.5*L:.4f} 0)'
        f' (stroke (width 0.1) (type default)) (fill (type none))))\n'
        f'    (symbol "SW_Push_1_1"\n'
        f'      (pin passive line (at {-L:.4f} 0 0) (length 0)\n'
        f'        (name "A" (effects (font (size 1.016 1.016))))\n'
        f'        (number "1" (effects (font (size 1.016 1.016)))))\n'
        f'      (pin passive line (at {L:.4f} 0 180) (length 0)\n'
        f'        (name "B" (effects (font (size 1.016 1.016))))\n'
        f'        (number "2" (effects (font (size 1.016 1.016)))))\n'
        f'  ))'
    )
    return sym_text, by_num


# ── Load library symbols ───────────────────────────────────────────────────────
print("Loading KiCad library symbols...")

msp430_sym, msp430_n, msp430_p = extract_sym(
    'MCU_Texas_MSP430', 'MSP430G2553IN20')
hc165_sym, hc165_n, hc165_p  = extract_sym('74xx', '74HC165')
lm386_sym, lm386_n, lm386_p  = extract_sym('Amplifier_Audio', 'LM386')
flash_sym, flash_n, flash_p   = extract_sym('Memory_Flash', 'W25Q128JVS')
r_lib_sym, _, r_lib_p         = extract_sym('Device', 'R')
c_lib_sym, _, c_lib_p         = extract_sym('Device', 'C')
spk_sym,   spk_n, spk_p      = extract_sym('Device', 'Speaker')
sw_sym,    sw_n,  sw_p       = extract_sym('Switch', 'SW_Push')
vcc_sym, _, _                 = extract_sym('power', 'VCC')
gnd_sym, _, _                 = extract_sym('power', 'GND')

# New symbols for OLED controller and LiPo charger circuits
tp4056_sym_txt, tp4056_n, tp4056_p = extract_sym('Battery_Management', 'TP4056-42-ESOP8')
dw01a_sym_txt, dw01a_n, dw01a_p    = extract_sym('Battery_Management', 'DW01A')
led_sym_txt,   led_n,   led_p      = extract_sym('Device', 'LED')
usb_sym_txt,   usb_n,   usb_p      = extract_sym('Connector', 'USB_B_Micro')
bat_sym_txt,   bat_n,   bat_p      = extract_sym('Connector', 'Conn_01x02_Pin')
nmos_sym_txt,  nmos_n,  nmos_p     = extract_sym('Transistor_FET', 'Q_NMOS_GSD')
oled_sym_txt,  oled_n,  oled_p    = extract_sym('Display_Graphic', 'OLED-128O064D')

print("TP4056 pins:", list(tp4056_n.keys()))
print("DW01A pins:", list(dw01a_n.keys()))
print("LED pins:", list(led_n.keys()))
print("USB_B_Micro pins:", list(usb_n.keys()))
print("Conn_01x02_Pin pins:", list(bat_n.keys()))
print("Q_NMOS_GSD pins:", list(nmos_n.keys()))
print("OLED-128O064D pins:", list(oled_n.keys()))

# ── Custom symbols (no KiCad library equivalent) ───────────────────────────────
sram_sym_txt, sram_n, sram_p = make_sram_sym()

R_LIB  = 'Device:R'
C_LIB  = 'Device:C'
rp     = r_lib_p   # pin_by_num for resistor
cp     = c_lib_p   # pin_by_num for capacitor

# ── Pin lookups ────────────────────────────────────────────────────────────────
# MSP430G2553IN20 — keyed by pin number (names are too long)
# From MCU_Texas_MSP430 library (Y-up local convention):
msp = {
    # Left-side pins (lx=-43.18, connects on left → lbl rot=180)
    'RST':  (-43.18,  11.43),
    'P2.0': (-43.18,   7.62),
    'P2.1': (-43.18,   5.08),
    'P2.2': (-43.18,   2.54),
    'P2.3': (-43.18,   0.00),
    'P2.4': (-43.18,  -2.54),
    'P2.5': (-43.18,  -5.08),
    'P2.6': (-43.18,  -7.62),
    'P2.7': (-43.18, -10.16),
    # Right-side pins (lx=+43.18, connects on right → lbl rot=0)
    'TEST': (43.18,  13.97),
    'P1.0': (43.18,  10.16),
    'P1.1': (43.18,   7.62),
    'P1.2': (43.18,   5.08),
    'P1.3': (43.18,   2.54),
    'P1.4': (43.18,   0.00),
    'P1.5': (43.18,  -2.54),
    'P1.6': (43.18,  -5.08),
    'P1.7': (43.18,  -7.62),
    # Power
    'DVCC': ( 0.00,  20.32),
    'DVSS': ( 0.00, -19.05),
}

# 74HC165 (via 74LS165 parent) — use library pin_by_name
# Key names from KiCad 74LS165 symbol:
hc = hc165_n   # {pin_name: (lx, ly)}
# Convenience: manually verify expected keys exist
for k in ['~{PL}', 'CP', 'D0', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7',
          'DS', '~{CE}', 'Q7', '~{Q7}', 'VCC', 'GND']:
    if k not in hc:
        print(f"  WARN: 74HC165 missing pin name '{k}' — using num fallback")

# LM386 — library pin_by_name
lm = lm386_n   # {pin_name: (lx, ly)}

# W25Q128JVS — library pin_by_name (from W25Q32JVSS parent)
fl = flash_n   # {pin_name: (lx, ly)}

# SRAM 23LC1024 — custom pin_by_name
sr = sram_n

# ── Component positions ── (all integer multiples of G = 2.54 mm) ─────────────
#
#  Layout (schematic, Y-down: larger y = lower):
#  B-size sheet ≈ 170G wide × 110G tall (432mm × 279mm)
#
#   J1(OLED)    U4(SRAM)      U5(Flash)   J2(LiPo)
#                        U1(MSP430)
#   Btns  U2(SR)                    U3(LM386)  C_OUT  LS1(Speaker)
#
# MSP430 left-pin endpoints at x = U1x - 43.18 = U1x - 17G
# MSP430 right-pin endpoints at x = U1x + 43.18 = U1x + 17G

U1  = (90*G,  70*G)   # MSP430G2553 — center of sheet (width 170G)
U2  = (42*G,  62*G)   # SN74HC165N  — D0-D7 pins at x=37G, y=57-64G
U3  = (150*G, 62*G)   # LM386       — far right
U4  = (70*G,  20*G)   # 23LC1024 SRAM — above MCU
U5  = (96*G,  20*G)   # W25Q128 Flash — above MCU
LS1 = (164*G, 62*G)   # Speaker — far right (sheet edge ~170G)

# OLED-128O064D display controller (replaces J1 placeholder)
# Symbol body spans ~30G tall; centered at (20G,28G) → top pins at y=13G, bottom at y=43G
DS1      = (20*G,   28*G)   # OLED-128O064D center
C_VDD    = (20*G,  10.5*G)  # 100nF VDD decoupling cap (vertical)
C_VBAT   = (19*G,  10.5*G)  # 1µF VBAT decoupling cap (vertical)
C_VCC_CP = (23.5*G, 13*G)   # 4.7µF charge-pump output cap (rot=90 horizontal)
C_VCOMH  = (11.5*G, 40*G)   # 4.7µF VCOMH decoupling cap (rot=90 horizontal)
C_C2     = (8.5*G,  16*G)   # 1µF flying cap C2 (rot=90 horizontal, to left of OLED)
C_C1     = (8.5*G,  19*G)   # 1µF flying cap C1 (rot=90 horizontal, 3G below C_C2)
R_IREF   = (12*G,  37.5*G)  # 910k IREF bias resistor (vertical)

# LiPo charger circuit positions (replaces J2 placeholder)
# Spread out for legibility: TP4056 and DW01A each get clear space;
# MOSFETs are separated by 8G; battery connector is at far right.
J4   = (120*G, 10*G)   # USB_B_Micro charge input
U7   = (140*G, 22*G)   # TP4056 charger IC
U8   = (140*G, 36*G)   # DW01A protection IC
Q1   = (150*G, 42*G)   # Q_NMOS_GSD discharge FET
Q2   = (158*G, 42*G)   # Q_NMOS_GSD charge FET
BT1  = (164*G, 40*G)   # Conn_01x02_Pin battery JST connector

# LiPo charger passives — properly spaced to match IC pin endpoints
C12  = (127*G, 10.5*G)  # 100nF VBUS decoupling (vertical, stubs from VBUS rail)
C13  = (130*G, 10.5*G)  # 10µF  VBUS decoupling (vertical)
R11  = (146.5*G, 23*G)  # 2k PROG resistor (rot=90 horizontal; aligns with PROG pin)
C14  = (146.5*G, 20*G)  # 10µF BAT filter (rot=90 horizontal; aligns with BAT pin)
D1   = (137.5*G, 22*G)  # LED red CHG indicator  (K=136G=~CHRG, A=139G)
D2   = (137.5*G, 23*G)  # LED green STDBY indicator (K=136G=~STDBY, A=139G)
R12  = (139*G,  20.5*G) # 1k CHG LED resistor (vertical; pin2=22G=D1.A exactly)
R13  = (140*G,  21.5*G) # 1k STDBY LED resistor (vertical; pin2=23G, wire→D2.A)

# Bypass caps — wired in parallel to IC VCC/GND pins via L-shaped wires.
C_MCU = (112*G, 70*G)  # 100nF bypass for MSP430  — right of U1
C_SR  = (50*G,  62*G)  # 100nF bypass for 74HC165 — right of U2 (clear of IC body)
C_SRM = (80*G,  20*G)  # 100nF bypass for SRAM    — right of U4
C_FLS = (104*G, 20*G)  # 100nF bypass for Flash   — right of U5

# Audio RC filter: PWM_OUT → R1 (1kΩ) → C5 (10µF) → LM386 + input (direct wire)
# Components placed adjacent to LM386 for minimal routing.
# R_AUD/C_AUD at half-G Y so pin endpoints land on integer-G grid.
# LM386 + input is at (147G, 61G); C5 pin2 aligns at y=61G → direct horizontal wire.
R_AUD = (143*G, 49.5*G)  # 1kΩ audio filter resistor
C_AUD = (143*G, 59.5*G)  # 10µF audio filter cap; pin2 at (143G, 61G) = LM386 + y
C_BYP = (150*G, 54*G)    # 10µF LM386 bypass — above BYPASS pin (150G, 59G)
C_OUT = (157*G, 62*G)    # 220µF output coupling — horizontal (rot=270), LM386→Speaker

# ── Button section layout ──────────────────────────────────────────────────────
# 8 switches at x=10G, 7G vertical spacing.
# Pull-up resistors form a horizontal comb at y=52.5G (half-G so pins land on G grid):
#   pin1 (VCC) at y=51G, pin2 (signal) at y=54G.
# VCC bus: horizontal wire at y=49G (x=18G→32G); VCC symbol at (18G, 47G).
# Each button routes via a "staircase" column wire to its HC165 D-pin and pull-up R,
# using direct wires only — no global labels on the HC165 data inputs.
BTN_X = 10*G
BTN_YS   = [n*G for n in [48, 55, 62, 69, 76, 83, 90, 97]]
BTN_NETS = ['BTN_A', 'BTN_B', 'BTN_C', 'BTN_D',
            'BTN_E', 'BTN_F', 'BTN_G', 'BTN_H']

# Staircase routing: (D_pin_name, y_D_G, R_x_G, staircase_x_G, SW_y_G)
# R_x_G: resistor center X.  staircase_x_G: column wire X (may be half-G).
# SW2 & SW3 share x=13G but have non-overlapping Y segments (gap at y=58G→59G).
BTN_ROUTES = [
    ('D0', 57, 32,   14.0, 48),   # SW1 / BTN_A
    ('D1', 58, 30,   13.0, 55),   # SW2 / BTN_B
    ('D2', 59, 28,   13.0, 62),   # SW3 / BTN_C
    ('D3', 60, 26,   13.5, 69),   # SW4 / BTN_D
    ('D4', 61, 24,   14.5, 76),   # SW5 / BTN_E
    ('D5', 62, 22,   16.0, 83),   # SW6 / BTN_F
    ('D6', 63, 20,   17.0, 90),   # SW7 / BTN_G
    ('D7', 64, 18,   18.0, 97),   # SW8 / BTN_H  (staircase_x == R_x)
]
R_COMB_Y  = 52.5 * G   # resistor center Y (half-G → pins at 51G top, 54G bottom)
R_TOP_Y   = 51   * G   # resistor pin 1 (VCC side)
R_BOT_Y   = 54   * G   # resistor pin 2 (signal side)
VCC_BUS_Y = 49   * G   # VCC rail that feeds all pull-up tops
R_XS = [32, 30, 28, 26, 24, 22, 20, 18]  # resistor X positions (G), D0→D7
HC_D_X = 37 * G        # HC165 D0-D7 pin endpoint X (all same for U2 at 42G)


# ── Grid check ────────────────────────────────────────────────────────────────
def chk(name, val):
    # Accept integer-G and half-G (0.5G) placements.
    # Half-G is used for passives (R, C) so their ±1.5G pin endpoints land on the G grid.
    r = val % G
    half_ok = abs(r - 0.5 * G) < 1e-9
    if r > 1e-9 and (G - r) > 1e-9 and not half_ok:
        print(f"  WARN: {name}={val:.4f} not on G or half-G grid (rem={r:.6f})")

for label, pt in [('U1', U1), ('U2', U2), ('U3', U3), ('U4', U4), ('U5', U5),
                   ('DS1', DS1), ('U7', U7), ('U8', U8),
                   ('J4', J4), ('BT1', BT1), ('Q1', Q1), ('Q2', Q2),
                   ('LS1', LS1),
                   ('C_MCU', C_MCU), ('C_SR', C_SR), ('C_SRM', C_SRM),
                   ('C_FLS', C_FLS), ('R_AUD', R_AUD), ('C_AUD', C_AUD),
                   ('C_BYP', C_BYP), ('C_OUT', C_OUT),
                   ('C_VDD', C_VDD), ('C_VBAT', C_VBAT), ('C_VCC_CP', C_VCC_CP),
                   ('C_VCOMH', C_VCOMH), ('C_C1', C_C1), ('C_C2', C_C2),
                   ('R_IREF', R_IREF),
                   ('C12', C12), ('C13', C13), ('R11', R11), ('C14', C14),
                   ('D1', D1), ('D2', D2), ('R12', R12), ('R13', R13)]:
    chk(f'{label}.x', pt[0])
    chk(f'{label}.y', pt[1])
chk('BTN_X', BTN_X)
chk('R_COMB_Y', R_COMB_Y)
chk('VCC_BUS_Y', VCC_BUS_Y)
for i, y in enumerate(BTN_YS):
    chk(f'BTN_Y[{i}]', y)
for i, rx in enumerate(R_XS):
    chk(f'R_X[{i}]', rx * G)
print("Grid check done.")


# ── Place ICs ─────────────────────────────────────────────────────────────────
place('MCU_Texas_MSP430:MSP430G2553IN20', *U1,  'U1', 'MSP430G2553')
place('74xx:74HC165',                     *U2,  'U2', 'SN74HC165N')
place('Amplifier_Audio:LM386',            *U3,  'U3', 'LM386N-1')
place('SRAM_23LC1024',                    *U4,  'U4', '23LC1024-I/P')
place('Memory_Flash:W25Q128JVS',          *U5,  'U5', 'W25Q128JVSSIQ')
place('Device:Speaker',                   *LS1, 'LS1', 'SP-3605')

# OLED-128O064D display and passives (replaces J1 connector)
# DS1 is the 30-pin KiCad Display_Graphic component: SPI 4-wire mode
# Flying caps C_C1/C_C2 connect the charge pump pins; IREF sets bias current.
place('Display_Graphic:OLED-128O064D',    *DS1,     'DS1', 'OLED-128O064D')
place(C_LIB, *C_VDD,    'C8',  '100nF 10V X5R')              # VDD decoupling
place(C_LIB, *C_VBAT,   'C9',  '1uF 10V X5R')               # VBAT decoupling
place(C_LIB, *C_VCC_CP, 'C10', '4.7uF 10V X5R', rot=90)     # charge pump output
place(C_LIB, *C_VCOMH,  'C11', '4.7uF 10V X5R', rot=90)     # VCOMH decoupling
place(C_LIB, *C_C2,     'C15', '1uF 10V X5R',   rot=90)     # flying cap C2
place(C_LIB, *C_C1,     'C16', '1uF 10V X5R',   rot=90)     # flying cap C1
place(R_LIB, *R_IREF,   'R10', '910k 1% 0402')              # IREF bias resistor

# LiPo charger circuit (replaces J2 connector)
# TP4056 charges from USB; DW01A+Q1/Q2 protect from over/under voltage and current.
place('Connector:USB_B_Micro',                *J4,  'J4',  'USB_B_Micro')
place('Battery_Management:TP4056-42-ESOP8',  *U7,  'U7',  'TP4056-42-ESOP8')
place('Battery_Management:DW01A',            *U8,  'U8',  'DW01A')
place('Transistor_FET:Q_NMOS_GSD',           *Q1,  'Q1',  'AO3400')  # discharge FET
place('Transistor_FET:Q_NMOS_GSD',           *Q2,  'Q2',  'AO3400')  # charge FET
place('Connector:Conn_01x02_Pin',            *BT1, 'BT1', 'LiPo_JST')
place(C_LIB, *C12, 'C12', '100nF 16V X7R')   # VBUS decoupling (vertical)
place(C_LIB, *C13, 'C13', '10uF  16V X5R')   # VBUS decoupling (vertical)
place(R_LIB, *R11, 'R11', '2k 1%',  rot=90)  # PROG resistor (horizontal)
place(C_LIB, *C14, 'C14', '10uF 10V X5R', rot=90)  # BAT filter (horizontal)
place('Device:LED', *D1, 'D1', 'LED_RED 0603')
place('Device:LED', *D2, 'D2', 'LED_GRN 0603')
place(R_LIB, *R12, 'R12', '1k 5%')  # CHG LED resistor (vertical)
place(R_LIB, *R13, 'R13', '1k 5%')  # STDBY LED resistor (vertical)

# Passives (using KiCad Device library)
place(C_LIB, *C_MCU, 'C1', '100nF')
place(C_LIB, *C_SR,  'C2', '100nF')
place(C_LIB, *C_SRM, 'C3', '100nF')
place(C_LIB, *C_FLS, 'C4', '100nF')
place(R_LIB, *R_AUD, 'R1', '1k')
place(C_LIB, *C_AUD, 'C5', '10uF')
place(C_LIB, *C_BYP, 'C6', '10uF')
place(C_LIB, *C_OUT, 'C7', '220uF', rot=270)  # horizontal: pin1=left(from amp), pin2=right(to spk)

# Switches (8 buttons, vertical column at BTN_X)
for i, (by, bnet) in enumerate(zip(BTN_YS, BTN_NETS), 1):
    place('Switch:SW_Push', BTN_X, by, f'SW{i}', bnet)

# Pull-up resistors: horizontal comb at y=52.5G
# R2=D0 at x=32G → R9=D7 at x=18G (2G pitch, matches HC165 D-pin staircase)
for i, rx_g in enumerate(R_XS, 2):
    place(R_LIB, rx_g * G, R_COMB_Y, f'R{i}', '10k')


# ── MSP430G2553 connections ───────────────────────────────────────────────────
def msp_w(pin):
    return pw(U1[0], U1[1], msp[pin][0], msp[pin][1])

pwr('VCC', *msp_w('DVCC'))
pwr('GND', *msp_w('DVSS'))
nc(*msp_w('P1.0'))                                          # LED1 (on LaunchPad)
nc(*msp_w('P1.1'))                                          # RXD (no UART in schematic)
lbl('PWM_OUT',  *msp_w('P1.2'), rot=0,   shape='output')    # PWM audio
nc(*msp_w('P1.3'))                                          # on-board button S2
nc(*msp_w('P1.4'))
lbl('SCK',      *msp_w('P1.5'), rot=0,   shape='output')   # SPI clock
lbl('MISO',     *msp_w('P1.6'), rot=0,   shape='input')    # SPI MISO
lbl('MOSI',     *msp_w('P1.7'), rot=0,   shape='output')   # SPI MOSI
lbl('OLED_CS',  *msp_w('P2.0'), rot=180, shape='output')   # OLED chip select
lbl('OLED_DC',  *msp_w('P2.1'), rot=180, shape='output')   # OLED data/cmd
lbl('OLED_RST', *msp_w('P2.2'), rot=180, shape='output')   # OLED reset
lbl('SRAM_CS',  *msp_w('P2.3'), rot=180, shape='output')   # SRAM chip select
lbl('FLASH_CS', *msp_w('P2.4'), rot=180, shape='output')   # Flash chip select
lbl('SH_LD',    *msp_w('P2.5'), rot=180, shape='output')   # SR parallel-load
nc(*msp_w('P2.6'))                                          # XIN
nc(*msp_w('P2.7'))                                          # XOUT
nc(*msp_w('RST'))
nc(*msp_w('TEST'))


# ── 74HC165 shift register connections ────────────────────────────────────────
def hc_w(pin_name):
    lx, ly = hc165_n.get(pin_name, hc165_p.get(pin_name, (None, None)))
    if lx is None:
        raise KeyError(f"74HC165 pin not found: '{pin_name}'")
    return pw(U2[0], U2[1], lx, ly)

lbl('SH_LD',  *hc_w('~{PL}'), rot=180, shape='input')    # parallel load (active low)
lbl('SCK',    *hc_w('CP'),    rot=180, shape='input')    # clock
# D0–D7: connected by staircase wires in the button section — no global labels here.
# DS (serial in) and ~CE (clock enable) both tied to GND via a shared bus at x=35.5G,
# then routed to the HC165 GND pin — one neat L-shaped connection for both inactive pins.
_hc_bus_x = 35.5 * G
_hc_ds    = hc_w('DS')        # (37G, 56G)
_hc_ce    = hc_w('~{CE}')    # (37G, 69G)
_hc_gnd   = hc_w('GND')      # (42G, 72G)
WIRES.append(_wire(_hc_ds[0],   _hc_ds[1],   _hc_bus_x,   _hc_ds[1]))   # DS → bus
WIRES.append(_wire(_hc_ce[0],   _hc_ce[1],   _hc_bus_x,   _hc_ce[1]))   # ~CE → bus
WIRES.append(_wire(_hc_bus_x,   _hc_ds[1],   _hc_bus_x,   _hc_gnd[1]))  # bus vertical
WIRES.append(_wire(_hc_bus_x,   _hc_gnd[1],  _hc_gnd[0],  _hc_gnd[1])) # bus → GND pin
WIRES.append(_wire(_hc_gnd[0],  _hc_gnd[1],  _hc_gnd[0],  74.5*G))      # stub to symbol
pwr('GND', _hc_gnd[0], 74.5*G)                                            # GND symbol
# T-junctions on the DS/CE GND bus
jct(_hc_bus_x, _hc_ce[1])      # ~CE wire meets vertical bus column
jct(_hc_gnd[0], _hc_gnd[1])    # bus horizontal meets GND pin stub
nc(           *hc_w('~{Q7}'))             # inverted output, not used
lbl('MISO',   *hc_w('Q7'),   rot=0, shape='output')   # serial out → MISO
pwr('VCC',    *hc_w('VCC'))


# ── LM386 connections ─────────────────────────────────────────────────────────
def lm_w(pin_name):
    lx, ly = lm386_n[pin_name]
    return pw(U3[0], U3[1], lx, ly)

# LM386 + input wired directly from C5 — see audio RC filter section below
pwr('GND',       *lm_w('-'))                  # inverting input → GND
pwr('VCC',       *lm_w('V+'))
pwr('GND',       *lm_w('GND'))
# BYPASS (pin 7) wired directly to C6 bottom — no label needed
# (C6 is positioned directly above this pin; wire added in bypass-cap section)
nc(*lm_w('GAIN'))                              # pin 1 GAIN (leave open = 20× gain)
# Pin 8 (GAIN) — same name as pin 1 in library; look up by number
lx8, ly8 = lm386_p['8']
nc(*pw(U3[0], U3[1], lx8, ly8))              # pin 8 GAIN
# LM386 output wired directly to C7 pin1 (left) — no label needed


# ── W25Q128JVS Flash connections ──────────────────────────────────────────────
def fl_w(pin_name):
    lx, ly = flash_n[pin_name]
    return pw(U5[0], U5[1], lx, ly)

lbl('FLASH_CS',  *fl_w('~{CS}'),              rot=180, shape='input')
lbl('MISO',      *fl_w('DO/IO_{1}'),          rot=180, shape='output')
pwr('VCC',       *fl_w('~{WP}/IO_{2}'))       # WP# → VCC (write protect disabled)
pwr('GND',       *fl_w('GND'))
lbl('MOSI',      *fl_w('DI/IO_{0}'),          rot=180, shape='input')
lbl('SCK',       *fl_w('CLK'),                rot=180, shape='input')
pwr('VCC',       *fl_w('~{HOLD}/~{RESET}/IO_{3}'))   # HOLD# → VCC
pwr('VCC',       *fl_w('VCC'))


# ── 23LC1024 SRAM connections ─────────────────────────────────────────────────
def sr_w(pin_name):
    lx, ly = sram_n[pin_name]
    return pw(U4[0], U4[1], lx, ly)

lbl('SRAM_CS', *sr_w('CS'),   rot=180, shape='input')
lbl('MISO',    *sr_w('SO'),   rot=180, shape='output')
nc(            *sr_w('NC'))
lbl('MOSI',    *sr_w('SI'),   rot=180, shape='input')
lbl('SCK',     *sr_w('SCK'),  rot=180, shape='input')
pwr('VCC',     *sr_w('HOLD'))              # HOLD# → VCC
pwr('VCC',     *sr_w('VCC'))
pwr('GND',     *sr_w('GND'))


# ── OLED-128O064D display DS1 (replaces J1 connector) ────────────────────────
# Component: KiCad Display_Graphic:OLED-128O064D (30-pin SSD1306-based display)
# Wired in SPI 4-wire mode: BS0=0, BS1=0, BS2=1.
# D0=SCK, D1=MOSI; D2-D7 not used (NC). R/~W and E/~RD unused (NC).
# Flying caps C_C1/C_C2: 1µF between C1P↔C1N and C2P↔C2N (charge pump).
# IREF: 910k to VCC sets bias current. VCOMH: 4.7µF to GND.
# DS1=(20G,28G): top pins y=13G, bottom pins y=43G, left pins x=15G.

def ds_w(pin_name):
    lx, ly = oled_n[pin_name]
    return pw(DS1[0], DS1[1], lx, ly)

# ── Top power pins: VDD (20G,13G), VBAT (19G,13G), VCC (21G,13G) ─────────────
# C_VDD at (20G,10.5G) vertical: pin1=(20G,9G)→VCC, pin2=(20G,12G)→wire→VDD(20G,13G)
_cvdd_p1 = pw(C_VDD[0],    C_VDD[1],    rp['1'][0], rp['1'][1])   # (20G, 9G)
_cvdd_p2 = pw(C_VDD[0],    C_VDD[1],    rp['2'][0], rp['2'][1])   # (20G, 12G)
pwr('VCC', *_cvdd_p1)
WIRES.append(_wire(*_cvdd_p2, *ds_w('VDD')))              # C_VDD pin2 → VDD(20G,13G)

# C_VBAT at (19G,10.5G) vertical: pin1=(19G,9G)→VCC, pin2=(19G,12G)→wire→VBAT(19G,13G)
_cvbat_p1 = pw(C_VBAT[0],  C_VBAT[1],  rp['1'][0], rp['1'][1])   # (19G, 9G)
_cvbat_p2 = pw(C_VBAT[0],  C_VBAT[1],  rp['2'][0], rp['2'][1])   # (19G, 12G)
pwr('VCC', *_cvbat_p1)
WIRES.append(_wire(*_cvbat_p2, *ds_w('VBAT')))            # C_VBAT pin2 → VBAT(19G,13G)

# C_VCC_CP at (23.5G,13G) rot=90 horizontal: pin1=(22G,13G)←VCC(21G,13G), pin2=(25G,13G)→GND
# VCC here is the charge pump OUTPUT — decoupling cap only, no external VCC supply.
_cvcp_p1 = (C_VCC_CP[0] - 1.5*G, C_VCC_CP[1])   # (22G, 13G)
_cvcp_p2 = (C_VCC_CP[0] + 1.5*G, C_VCC_CP[1])   # (25G, 13G)
WIRES.append(_wire(*ds_w('VCC'), *_cvcp_p1))              # VCC(21G,13G) → cap pin1
pwr('GND', *_cvcp_p2)                                     # cap pin2 → GND

# ── Flying capacitors: C2P↔C2N and C1P↔C1N ───────────────────────────────────
# Pin pairs are 1G (2.54mm) apart — can't connect directly (cap body = 3G).
# Place cap horizontal, L-shaped routing:
#   near pin (Cx_P) → straight horizontal to cap pin2 (right side of cap)
#   far  pin (Cx_N) → horizontal left, then vertical to cap pin1 (left side of cap)
#
# C_C2 at (8.5G,16G) rot=90 horiz: pin1=(7G,16G), pin2=(10G,16G)
# C2P(15G,16G)→ horiz →pin2(10G,16G)
# C2N(15G,15G)→ horiz →(7G,15G)→ vert ↓→pin1(7G,16G)
_cc2_p1 = (C_C2[0] - 1.5*G, C_C2[1])   # (7G, 16G)
_cc2_p2 = (C_C2[0] + 1.5*G, C_C2[1])   # (10G, 16G)
WIRES.append(_wire(*ds_w('C2P'), *_cc2_p2))               # C2P → C_C2.pin2
WIRES.append(_wire(*ds_w('C2N'), 7*G, ds_w('C2N')[1]))    # C2N left to x=7G
WIRES.append(_wire(7*G, ds_w('C2N')[1], *_cc2_p1))        # then down to C_C2.pin1

# C_C1 at (8.5G,19G) rot=90 horiz: pin1=(7G,19G), pin2=(10G,19G)
# C_C1 is 3G below C_C2 so they don't overlap (C_C2 spans 14.5G–17.5G, C_C1 spans 17.5G–20.5G).
# C1P(15G,17G)→ horiz left →(10G,17G)→ vert down →pin2(10G,19G)
# C1N(15G,18G)→ horiz left →(7G,18G) → vert down →pin1(7G,19G)
_cc1_p1 = (C_C1[0] - 1.5*G, C_C1[1])   # (7G, 19G)
_cc1_p2 = (C_C1[0] + 1.5*G, C_C1[1])   # (10G, 19G)
WIRES.append(_wire(*ds_w('C1P'), _cc1_p2[0], ds_w('C1P')[1]))  # C1P horiz → x=10G
WIRES.append(_wire(_cc1_p2[0], ds_w('C1P')[1], *_cc1_p2))      # then vert ↓ to cap pin2
WIRES.append(_wire(*ds_w('C1N'), 7*G, ds_w('C1N')[1]))          # C1N horiz left to x=7G
WIRES.append(_wire(7*G, ds_w('C1N')[1], *_cc1_p1))              # then vert ↓ to cap pin1

# ── Bus select (SPI 4-wire): BS0=0, BS1=0, BS2=1 ─────────────────────────────
pwr('GND', *ds_w('BS0'))
pwr('GND', *ds_w('BS1'))
pwr('VCC', *ds_w('BS2'))

# ── SPI control signals → global labels ───────────────────────────────────────
lbl('OLED_CS',  *ds_w('~{CS}'),   rot=180, shape='input')
lbl('OLED_RST', *ds_w('~{RES}'),  rot=180, shape='input')
lbl('OLED_DC',  *ds_w('D/~{C}'), rot=180, shape='input')

# ── Parallel-interface pins unused in SPI mode → NC ──────────────────────────
nc(*ds_w('R/~{W}'))
nc(*ds_w('E/~{RD}'))

# ── SPI data bus: D0=SCK, D1=MOSI; D2-D7 → NC ───────────────────────────────
lbl('SCK',  *ds_w('D0'), rot=180, shape='input')
lbl('MOSI', *ds_w('D1'), rot=180, shape='input')
for _dp in ['D2', 'D3', 'D4', 'D5', 'D6', 'D7']:
    nc(*ds_w(_dp))

# ── IREF bias resistor R10: (12G,37.5G) vertical ─────────────────────────────
# pin1=(12G,36G)→VCC; pin2=(12G,39G)→horizontal wire 3G right→IREF(15G,39G)
_riref_p1 = pw(R_IREF[0], R_IREF[1], rp['1'][0], rp['1'][1])   # (12G, 36G)
_riref_p2 = pw(R_IREF[0], R_IREF[1], rp['2'][0], rp['2'][1])   # (12G, 39G)
pwr('VCC', *_riref_p1)
WIRES.append(_wire(*_riref_p2, *ds_w('IREF')))    # (12G,39G)→(15G,39G)=IREF

# ── VCOMH decoupling cap C11: (11.5G,40G) rot=90 horizontal ──────────────────
# pin1=(10G,40G)→GND; pin2=(13G,40G)→horizontal wire 2G right→VCOMH(15G,40G)
_cvch_p1 = (C_VCOMH[0] - 1.5*G, C_VCOMH[1])   # (10G, 40G)
_cvch_p2 = (C_VCOMH[0] + 1.5*G, C_VCOMH[1])   # (13G, 40G)
pwr('GND', *_cvch_p1)
WIRES.append(_wire(*_cvch_p2, *ds_w('VCOMH')))    # (13G,40G)→(15G,40G)=VCOMH

# ── Right-side NC pin and bottom GND pins ─────────────────────────────────────
nc(*ds_w('NC'))
pwr('GND', *ds_w('GND'))
pwr('GND', *ds_w('VSS'))
pwr('GND', *ds_w('VLSS'))


# ── LiPo charger + protection circuit (replaces J2 connector) ─────────────────
# Topology:
#   USB 5V → J4 → VBUS rail → TP4056 V_CC
#   TP4056 BAT → VBAT net → DW01A VCC → battery positive
#   TP4056 ~CHRG/~STDBY (open-drain) → LED indicators (D1/D2 with R12/R13 to VCC)
#   DW01A OD → Q1.G (discharge FET); DW01A OC → Q2.G (charge FET)
#   Back-to-back NMOS: Q1.D↔Q2.D; Q1.S=B- (battery−); Q2.S=circuit GND
#   DW01A CS → GND (current sense at circuit negative)
#   Battery connector BT1: Pin_1=VBAT (+), Pin_2=B- (−, through protection FETs)

# ── J4 USB_B_Micro connections ────────────────────────────────────────────────
# Pins (at J4=(120G,10G)): VBUS=(123G,8G), D+=(123G,10G), D-=(123G,11G),
#                           ID=(123G,12G), GND=(120G,14G), Shield=(119G,14G)
_j4_vbus   = pw(J4[0], J4[1], usb_n['VBUS'][0],   usb_n['VBUS'][1])    # (123G, 8G)
_j4_gnd    = pw(J4[0], J4[1], usb_n['GND'][0],    usb_n['GND'][1])     # (120G, 14G)
_j4_shield = pw(J4[0], J4[1], usb_n['Shield'][0], usb_n['Shield'][1])  # (119G, 14G)
pwr('GND', *_j4_gnd)
pwr('GND', *_j4_shield)
nc(*pw(J4[0], J4[1], usb_n['D+'][0], usb_n['D+'][1]))
nc(*pw(J4[0], J4[1], usb_n['D-'][0], usb_n['D-'][1]))
nc(*pw(J4[0], J4[1], usb_n['ID'][0], usb_n['ID'][1]))
# VBUS net label at J4.VBUS pin — names the 5V USB power domain explicitly
lbl('VBUS', *_j4_vbus, rot=180, shape='output')

# VBUS rail: horizontal at y=8G from J4.VBUS (123G,8G) → (140G,8G);
#            then vertical (140G,8G) → (140G,17G) = TP4056 V_CC pin.
WIRES.append(_wire(*_j4_vbus, 140*G, _j4_vbus[1]))          # horizontal
WIRES.append(_wire(140*G, _j4_vbus[1], 140*G, 17*G))        # vertical to V_CC

# C12 (100nF) and C13 (10µF): VBUS decoupling caps, stub down from VBUS rail.
# Cap centers at (127G,10.5G) and (130G,10.5G); pin1=top(9G), pin2=bottom(12G)→GND.
_c12_p1 = pw(C12[0], C12[1], cp['1'][0], cp['1'][1])   # (127G, 9G)
_c12_p2 = pw(C12[0], C12[1], cp['2'][0], cp['2'][1])   # (127G, 12G)
_c13_p1 = pw(C13[0], C13[1], cp['1'][0], cp['1'][1])   # (130G, 9G)
_c13_p2 = pw(C13[0], C13[1], cp['2'][0], cp['2'][1])   # (130G, 12G)
WIRES.append(_wire(127*G, _j4_vbus[1], *_c12_p1))       # rail stub → C12 pin1
WIRES.append(_wire(130*G, _j4_vbus[1], *_c13_p1))       # rail stub → C13 pin1
pwr('GND', *_c12_p2)
pwr('GND', *_c13_p2)
# T-junctions where decoupling cap stubs branch off the VBUS rail
jct(127*G, _j4_vbus[1])   # C12 stub T-junction on VBUS rail
jct(130*G, _j4_vbus[1])   # C13 stub T-junction on VBUS rail
jct(140*G, _j4_vbus[1])   # VBUS rail → vertical to V_CC T-junction

# ── TP4056 U7 connections ─────────────────────────────────────────────────────
# Pins at U7=(140G,22G): V_CC=(140G,17G), CE=(136G,20G), BAT=(144G,20G),
#   ~CHRG=(136G,22G), TEMP=(144G,22G), ~STDBY=(136G,23G), PROG=(144G,23G),
#   EPAD=(139G,27G), GND=(140G,27G)
def _tp_w(pin_name):
    lx, ly = tp4056_n[pin_name]
    return pw(U7[0], U7[1], lx, ly)

# V_CC: wired from VBUS rail above (140G,8G)→(140G,17G) — already added.
# GND and EPAD → GND
pwr('GND', *_tp_w('GND'))
pwr('GND', *_tp_w('EPAD'))
# CE(136G,20G) → VBUS (tie high to always enable charging; CE is V_CC-domain signal,
# not MCU VCC/3.3V — use VBUS label so CE references the 5V USB supply correctly)
lbl('VBUS', *_tp_w('CE'), rot=180, shape='input')
# TEMP(144G,22G) → VBUS (no NTC thermistor; tie to V_CC rail so thermal threshold
# ratio TEMP/V_CC = 100%, defeating the thermal guard and keeping charging always enabled.
# Using VCC/3.3V here would give ratio 66% which is inside the 45–80% normal range but
# would falsely trigger a charge-inhibit if the 3.3V rail dips under 2.25V.)
lbl('VBUS', *_tp_w('TEMP'), rot=0, shape='input')

# BAT(144G,20G) → VBAT label (battery+); also C14 filter cap to GND
lbl('VBAT', *_tp_w('BAT'), rot=0, shape='passive')
# C14 at (146.5G,20G) rot=90 horizontal: pin1=(145G,20G), pin2=(148G,20G)→GND
_c14_p1 = (C14[0] - 1.5*G, C14[1])   # (145G, 20G)
_c14_p2 = (C14[0] + 1.5*G, C14[1])   # (148G, 20G)
WIRES.append(_wire(*_tp_w('BAT'), *_c14_p1))     # BAT(144G,20G) → C14.pin1(145G,20G)
pwr('GND', *_c14_p2)                             # C14.pin2 → GND

# PROG(144G,23G) → R11 → GND
# R11 at (146.5G,23G) rot=90 horizontal: pin1=(145G,23G), pin2=(148G,23G)→GND
_r11_p1 = (R11[0] - 1.5*G, R11[1])   # (145G, 23G)
_r11_p2 = (R11[0] + 1.5*G, R11[1])   # (148G, 23G)
WIRES.append(_wire(*_tp_w('PROG'), *_r11_p1))    # PROG(144G,23G) → R11.pin1
pwr('GND', *_r11_p2)                             # R11.pin2 → GND

# ~CHRG(136G,22G) → D1.K (D1 center at (137.5G,22G), K=(136G,22G) = same point, no wire)
# ~STDBY(136G,23G) → D2.K (D2 center at (137.5G,23G), K=(136G,23G) = same point, no wire)
# D1.A=(139G,22G) = R12.pin2 exactly (no wire)
# D2.A=(139G,23G) ← 1G wire from R13.pin2=(140G,23G)

# R12 at (139G,20.5G) vertical (rot=0): pin1=(139G,19G)→VCC, pin2=(139G,22G)=D1.A
_r12_p1 = pw(R12[0], R12[1], rp['1'][0], rp['1'][1])   # (139G, 19G)
_r12_p2 = pw(R12[0], R12[1], rp['2'][0], rp['2'][1])   # (139G, 22G) — is D1.A exactly
pwr('VCC', *_r12_p1)
# No wire needed: R12.pin2 and D1.A share coordinate (139G,22G)

# R13 at (140G,21.5G) vertical (rot=0): pin1=(140G,20G)→VCC, pin2=(140G,23G)→wire→D2.A(139G,23G)
_r13_p1 = pw(R13[0], R13[1], rp['1'][0], rp['1'][1])   # (140G, 20G)
_r13_p2 = pw(R13[0], R13[1], rp['2'][0], rp['2'][1])   # (140G, 23G)
pwr('VCC', *_r13_p1)
WIRES.append(_wire(*_r13_p2, 139*G, 23*G))   # R13.pin2(140G,23G) → D2.A(139G,23G)

# ── DW01A U8 connections ──────────────────────────────────────────────────────
# Pins at U8=(140G,36G): VCC=(136G,35G), TD=(144G,35G), GND=(136G,37G),
#   CS=(144G,37G), OD=(139G,39G), OC=(141G,39G)
def _dw_w(pin_name):
    lx, ly = dw01a_n[pin_name]
    return pw(U8[0], U8[1], lx, ly)

lbl('VBAT', *_dw_w('VCC'), rot=180, shape='passive')   # VCC(136G,35G) → VBAT label
pwr('GND',  *_dw_w('GND'))                              # GND(136G,37G) → GND
nc(         *_dw_w('TD'))                               # TD (test) → NC
pwr('GND',  *_dw_w('CS'))                               # CS(144G,37G) → GND (sense point)

# OD(139G,39G) → Q1.G(148G,42G): L-shape down→right→up
_od_w = _dw_w('OD')    # (139G, 39G)
_q1_g = pw(Q1[0], Q1[1], nmos_n['G'][0], nmos_n['G'][1])   # (148G, 42G)
WIRES.append(_wire(*_od_w,          _od_w[0], 43*G))         # down to y=43G
WIRES.append(_wire(_od_w[0], 43*G, _q1_g[0], 43*G))         # right to Q1.G x
WIRES.append(_wire(_q1_g[0], 43*G, *_q1_g))                  # up to Q1.G(148G,42G)

# OC(141G,39G) → Q2.G(156G,42G): L-shape down→right→up
_oc_w = _dw_w('OC')    # (141G, 39G)
_q2_g = pw(Q2[0], Q2[1], nmos_n['G'][0], nmos_n['G'][1])   # (156G, 42G)
WIRES.append(_wire(*_oc_w,          _oc_w[0], 45*G))         # down to y=45G
WIRES.append(_wire(_oc_w[0], 45*G, _q2_g[0], 45*G))         # right to Q2.G x
WIRES.append(_wire(_q2_g[0], 45*G, *_q2_g))                  # up to Q2.G(156G,42G)

# ── Back-to-back NMOS protection FETs ────────────────────────────────────────
# Q1=(150G,42G): G=(148G,42G), D=(151G,40G), S=(151G,44G)
# Q2=(158G,42G): G=(156G,42G), D=(159G,40G), S=(159G,44G)
_q1_d = pw(Q1[0], Q1[1], nmos_n['D'][0], nmos_n['D'][1])   # (151G, 40G)
_q1_s = pw(Q1[0], Q1[1], nmos_n['S'][0], nmos_n['S'][1])   # (151G, 44G)
_q2_d = pw(Q2[0], Q2[1], nmos_n['D'][0], nmos_n['D'][1])   # (159G, 40G)
_q2_s = pw(Q2[0], Q2[1], nmos_n['S'][0], nmos_n['S'][1])   # (159G, 44G)

# Drain-to-drain connection (back-to-back topology)
WIRES.append(_wire(*_q1_d, *_q2_d))    # (151G,40G) → (159G,40G)

# Q2.S → GND (circuit negative; DW01A.CS is already tied here)
pwr('GND', *_q2_s)                     # (159G, 44G) → GND

# ── Battery connector BT1 connections ─────────────────────────────────────────
# BT1=(164G,40G): Pin_1=(166G,40G) → VBAT+, Pin_2=(166G,41G) → battery−(B-)
_bt1_p1 = pw(BT1[0], BT1[1], bat_n['Pin_1'][0], bat_n['Pin_1'][1])   # (166G, 40G)
_bt1_p2 = pw(BT1[0], BT1[1], bat_n['Pin_2'][0], bat_n['Pin_2'][1])   # (166G, 41G)
lbl('VBAT', *_bt1_p1, rot=0, shape='passive')   # Pin_1 → VBAT (battery positive)

# Pin_2 (battery−) → Q1.S(151G,44G): route right→down→left→up
# (166G,41G)→(166G,46G)→(151G,46G)→(151G,44G)
WIRES.append(_wire(*_bt1_p2,        166*G, 46*G))     # down to y=46G
WIRES.append(_wire(166*G, 46*G,     151*G, 46*G))     # left to Q1.S x=151G
WIRES.append(_wire(151*G, 46*G,     *_q1_s))          # up to Q1.S(151G,44G)


# ── Speaker LS1 (Device:Speaker, both pins on left side) ──────────────────────
# Speaker pin1 wired directly from C7 pin2 (right) — wire added in audio-output section
pwr('GND',     *pw(LS1[0], LS1[1], spk_p['2'][0], spk_p['2'][1]))


# ── Audio RC filter chain ─────────────────────────────────────────────────────
# PWM_OUT → R1 (1kΩ) → C5 (10µF) → LM386 + input (direct horizontal wire).
# No mid-chain global labels — all connections use wires.
# R1 and C5 placed adjacent to LM386 so C5 pin2 aligns at the same Y as LM386 +.
_r1_top  = pw(R_AUD[0], R_AUD[1], rp['1'][0], rp['1'][1])  # (143G, 48G)
_r1_bot  = pw(R_AUD[0], R_AUD[1], rp['2'][0], rp['2'][1])  # (143G, 51G)
_c5_top  = pw(C_AUD[0], C_AUD[1], cp['1'][0], cp['1'][1])  # (143G, 58G)
_c5_bot  = pw(C_AUD[0], C_AUD[1], cp['2'][0], cp['2'][1])  # (143G, 61G)
_lm_plus = lm_w('+')                                        # (147G, 61G)
lbl('PWM_OUT', *_r1_top, rot=90, shape='input')             # label at top of R1 (receiving PWM from MCU)
WIRES.append(_wire(*_r1_bot, *_c5_top))                     # R1 bottom → C5 top
WIRES.append(_wire(*_c5_bot, *_lm_plus))                    # C5 bottom → LM386 + (horizontal)


# ── Bypass capacitors — wired in parallel to IC power pins ───────────────────
# Each cap sits adjacent to its IC. L-shaped wires run from the IC's VCC/GND
# pin endpoints to the cap terminals. The IC's VCC/GND power symbols (placed
# above in the IC connection sections) share the net via those same endpoints.
wire_bypass_cap(C_MCU, msp_w('DVCC'), msp_w('DVSS'))
wire_bypass_cap(C_SR,  hc_w('VCC'),   hc_w('GND'))
wire_bypass_cap(C_SRM, sr_w('VCC'),   sr_w('GND'))
wire_bypass_cap(C_FLS, fl_w('VCC'),   fl_w('GND'))

# C6 — LM386 bypass cap: VCC on top, bottom wired to BYPASS pin (pin 7)
pwr('VCC', *pw(C_BYP[0], C_BYP[1], cp['1'][0], cp['1'][1]))
c6_bot  = pw(C_BYP[0], C_BYP[1], cp['2'][0], cp['2'][1])
bypass  = lm_w('BYPASS')
WIRES.append(_wire(*c6_bot, *bypass))

# C7 — output coupling cap (horizontal, rot=270): pin1=left, pin2=right
# Wired: LM386 output → C7 pin1 → C7 pin2 → Speaker pin1
# Device:C at rot=270: pin1 offset (-1.5G, 0), pin2 offset (+1.5G, 0)
c7_p1 = (C_OUT[0] - 1.5*G, C_OUT[1])   # left  (connects to LM386 output)
c7_p2 = (C_OUT[0] + 1.5*G, C_OUT[1])   # right (connects to speaker pin1)
lm_out = lm_w('~')
spk_in = pw(LS1[0], LS1[1], spk_p['1'][0], spk_p['1'][1])
WIRES.append(_wire(*lm_out, *c7_p1))    # LM386 → C7 left
WIRES.append(_wire(*c7_p2,  *spk_in))   # C7 right → Speaker pin1


# ── VCC bus + pull-up resistor comb ───────────────────────────────────────────
# Horizontal VCC bus at y=49G connects all 8 resistor tops (y=51G) via short stubs.
WIRES.append(_wire(18*G, VCC_BUS_Y, 32*G, VCC_BUS_Y))   # VCC rail x=18G→32G
pwr('VCC', 18*G, 47*G)                                    # VCC symbol at left end
WIRES.append(_wire(18*G, 47*G, 18*G, VCC_BUS_Y))         # symbol stub to rail
for rx_g in R_XS:
    WIRES.append(_wire(rx_g*G, VCC_BUS_Y, rx_g*G, R_TOP_Y))  # rail → R pin1
# T-junctions: every resistor stub branches off the VCC rail
# R8 (D7) is at x=18G which is also where the VCC symbol stub meets the rail —
# that's a 3-way junction too. R2 (D0) is at x=32G — end of rail, 2-wire corner, no jct needed.
for rx_g in R_XS[1:]:    # skip R2 (x=32G, rail end — corner not T)
    jct(rx_g * G, VCC_BUS_Y)

# ── Staircase button wiring ────────────────────────────────────────────────────
# For each button, three wire segments form the staircase:
#   1. Switch pin2 → staircase column (short horizontal)
#   2. Staircase column vertical (switch Y ↔ D-pin Y)
#   3. D-pin horizontal: staircase → resistor column → HC165 (two segments if sX≠rX)
# Resistor column (rX, R_BOT_Y=54G) → (rX, yD) closes the loop to the D-pin.
# Switch pin1 gets GND directly (no stub wire; power symbol sits at pin endpoint).
for _dpin, yD_g, rX_g, sX_g, swY_g in BTN_ROUTES:
    yD  = yD_g  * G
    rX  = rX_g  * G
    sX  = sX_g  * G
    swY = swY_g * G

    # Switch GND (pin 1 endpoint)
    pwr('GND', *pw(BTN_X, swY, sw_p['1'][0], sw_p['1'][1]))

    # Switch pin2 → staircase column
    sw_p2x = pw(BTN_X, swY, sw_p['2'][0], sw_p['2'][1])[0]
    WIRES.append(_wire(sw_p2x, swY, sX, swY))

    # Staircase vertical (may go up or down depending on switch vs D-pin position)
    y_lo, y_hi = (yD, swY) if yD < swY else (swY, yD)
    WIRES.append(_wire(sX, y_lo, sX, y_hi))

    # D-pin horizontal: staircase → resistor column (omit if same column)
    if abs(sX - rX) > 0.001:
        WIRES.append(_wire(sX, yD, rX, yD))

    # Resistor column: R pin2 (54G) → D-pin level (if D-pin is below R_BOT_Y)
    if yD > R_BOT_Y:
        WIRES.append(_wire(rX, R_BOT_Y, rX, yD))

    # D-pin horizontal: resistor/junction → HC165 endpoint
    WIRES.append(_wire(rX, yD, HC_D_X, yD))

    # T-junction at (rX, yD): R column wire, staircase/horizontal, and D-pin wire all meet
    jct(rX, yD)


# ── Assemble lib_symbols block ────────────────────────────────────────────────
lib_block = '\n'.join([
    msp430_sym,
    hc165_sym,
    lm386_sym,
    flash_sym,
    r_lib_sym,
    c_lib_sym,
    spk_sym,
    sw_sym,
    sram_sym_txt,
    vcc_sym,
    gnd_sym,
    oled_sym_txt,        # Display_Graphic:OLED-128O064D (replaces hand-coded SSD1306)
    tp4056_sym_txt,
    dw01a_sym_txt,
    led_sym_txt,
    usb_sym_txt,
    bat_sym_txt,
    nmos_sym_txt,
])

all_elements = '\n'.join(
    f'  {e}' for e in (PLACED + WIRES + LABELS + POWERS + NC + JUNCTIONS)
)

# ── Build schematic ────────────────────────────────────────────────────────────
sch = f"""(kicad_sch
  (version 20250114)
  (generator "python-script")
  (generator_version "9.0")
  (uuid "{SCH_UUID}")
  (paper "B")
  (title_block
    (title "MSP430G2553 Handheld Game Console")
    (date "{_TODAY}")
    (rev "5.0")
    (company "")
    (comment 1 "MCU: MSP430G2553 (LaunchPad MSP-EXP430G2ET)")
    (comment 2 "SPI bus (USCI_B0): P1.5=SCK  P1.6=MISO  P1.7=MOSI")
    (comment 3 "CS: P2.0=OLED_CS  P2.1=OLED_DC  P2.2=OLED_RST  P2.3=SRAM_CS  P2.4=FLASH_CS  P2.5=SH/LD#")
    (comment 4 "Buttons: 74HC165 parallel-in/serial-out, 10k pull-ups to VCC, BTN_A..H")
  )
  (lib_symbols
{lib_block}
  )
{all_elements}
  (sheet_instances
    (path "/" (page "1"))
  )
)
"""

# ── Validate ──────────────────────────────────────────────────────────────────
opens  = sch.count('(')
closes = sch.count(')')
assert opens == closes, f"PAREN MISMATCH: {opens} open vs {closes} close"

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUT_PATH.write_text(sch)

print(f"Written: {OUT_PATH}")
print(f"  Size:   {OUT_PATH.stat().st_size:,} bytes")
print(f"  Lines:  {sch.count(chr(10))}")
print(f"  Parens: {opens} open = {closes} close ✓")
print(f"  Placed: {len(PLACED)}  Wires: {len(WIRES)}"
      f"  Labels: {len(LABELS)}  Powers: {len(POWERS)}  NC: {len(NC)}"
      f"  Junctions: {len(JUNCTIONS)}")

# KiCad 9 format audit
checks = [
    ('version 20250114',   '(version 20250114)' in sch),
    ('generator_version',  '"9.0"' in sch),
    ('exclude_from_sim',   'exclude_from_sim' in sch),
    ('dnp field',          '(dnp no)' in sch),
    ('fields_autoplaced',  'fields_autoplaced' in sch),
    ('justify left',       'justify left' in sch),
]
for name, ok in checks:
    print(f"  {'✓' if ok else '✗'} {name}")

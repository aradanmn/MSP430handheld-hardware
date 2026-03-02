"""
gen_kicad6.py — MSP430G2553 Game Boy schematic generator
Target: KiCad 9.0.7 native format (version 20250114)

Format research (from accessible KiCad sources, 2026-03-01):
  sch_file_versions.h documents these version milestones:
    20231120 — generator_version field introduced (KiCad 8.0)
    20241004 — 'hide' changed from (hide yes) to bare boolean (hide)
    20241209 — private flags for SCH_FIELDs
    20250114 — full paths for text variable cross references (KiCad 9.0)
  KiCad 9 placed symbols require: exclude_from_sim, dnp fields
  KiCad 9 labels: (fields_autoplaced yes), (justify left) always

Coordinate system:
  Symbol local coords: Y increases UP (math convention)
  Schematic world coords: Y increases DOWN (screen convention)
  Mapping: world = (cx + lx,  cy - ly)   [Y is NEGATED]

Connection strategy:
  Every net label has a 2.54mm wire stub from pin endpoint.
  Pin endpoint is at (cx+lx, cy-ly). Label is 2.54mm further out.
  This makes connections unambiguous visually.
"""
import uuid as _uuid

def uid():
    return str(_uuid.uuid4())

# ─── Coordinate helpers ───────────────────────────────────────────────────────
def pw(cx, cy, lx, ly):
    """World coords for a pin at symbol-local (lx, ly), component at (cx,cy)."""
    return (round(cx + lx, 4), round(cy - ly, 4))

# ─── S-expression emitters ────────────────────────────────────────────────────
def _wire(x1, y1, x2, y2):
    return (f'(wire (pts (xy {x1:.4f} {y1:.4f}) (xy {x2:.4f} {y2:.4f}))'
            f' (stroke (width 0) (type default)) (uuid "{uid()}"))')

def _label(net, x, y, rot=0):
    """KiCad 9 net label. Connection point IS at (x,y). Always justify left."""
    return (f'(label "{net}" (at {x:.4f} {y:.4f} {rot})'
            f' (fields_autoplaced yes)'
            f' (effects (font (size 1.27 1.27)) (justify left))'
            f' (uuid "{uid()}"))')

def _power(sym, x, y):
    """KiCad 9 power symbol placed with pin at exactly (x,y)."""
    # VCC: body above pin (pin at bottom), GND: body below pin (pin at top)
    ref_off = -2.54 if sym == 'VCC' else 2.54
    return (f'(symbol (lib_id "{sym}") (at {x:.4f} {y:.4f} 0)'
            f' (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)'
            f' (uuid "{uid()}")'
            f' (property "Reference" "#PWR" (at {x:.4f} {y+ref_off:.4f} 0)'
            f'  (effects (font (size 1.27 1.27)) (hide)))'
            f' (property "Value" "{sym}" (at {x:.4f} {y-ref_off:.4f} 0)'
            f'  (effects (font (size 1.27 1.27)) (hide)))'
            f')')

def _no_connect(x, y):
    return f'(no_connect (at {x:.4f} {y:.4f}) (uuid "{uid()}"))'

def _placed_sym(lib_id, cx, cy, ref, val, rot=0):
    """KiCad 9 placed symbol instance. Ref/Value hidden to avoid clutter."""
    return (f'(symbol (lib_id "{lib_id}") (at {cx:.4f} {cy:.4f} {rot})'
            f' (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)'
            f' (uuid "{uid()}")'
            f' (property "Reference" "{ref}"'
            f'  (at {cx:.4f} {cy:.4f} 0) (effects (font (size 1.27 1.27)) (hide)))'
            f' (property "Value" "{val}"'
            f'  (at {cx:.4f} {cy:.4f} 0) (effects (font (size 1.27 1.27)) (hide)))'
            f')')

# ─── Accumulator lists ────────────────────────────────────────────────────────
PLACED = []
WIRES  = []
LABELS = []
POWERS = []
NC     = []

STUB = 2.54  # wire stub length in mm

def lbl(net, px, py, rot=0):
    """Label with stub wire. Pin endpoint at (px,py); label stub extends outward."""
    if   rot == 0:   ex, ey = px + STUB, py   # right-side pin → label to the right
    elif rot == 180: ex, ey = px - STUB, py   # left-side pin  → label to the left
    elif rot == 90:  ex, ey = px, py + STUB   # bottom pin     → label below
    elif rot == 270: ex, ey = px, py - STUB   # top pin        → label above
    else:            ex, ey = px, py
    WIRES.append(_wire(px, py, ex, ey))
    LABELS.append(_label(net, ex, ey, rot))

def pwr(sym, px, py):
    POWERS.append(_power(sym, px, py))

def nc(px, py):
    NC.append(_no_connect(px, py))

def place(lib_id, cx, cy, ref, val, rot=0):
    PLACED.append(_placed_sym(lib_id, cx, cy, ref, val, rot))

# ─── Symbol geometry builder ──────────────────────────────────────────────────
def ic_sym(name, left_pins, right_pins, body_hw=5.08, ref_prefix='U'):
    """
    Build a KiCad 9 lib symbol for a generic IC.
    left_pins / right_pins: list of (pin_name, pin_type).
    Pin pitch: 2.54mm, centred. Endpoint offset: ±(body_hw + 2.54)mm.
    Returns (symbol_text, pin_dict) where pin_dict maps name → (lx, ly).
    KiCad 9 'hide' syntax: bare (hide) not (hide yes).
    """
    n_left  = len(left_pins)
    n_right = len(right_pins)
    n = max(n_left, n_right)
    half = (n - 1) * 1.27          # ± half-span, pin pitch=2.54
    body_h = half + 1.27
    px = body_hw + 2.54            # pin endpoint offset from centre

    pin_dict = {}
    pins_str = ''
    num = 1

    for i, (pname, ptype) in enumerate(left_pins):
        ly = half - i * 2.54
        lx = -px
        pin_dict[pname] = (lx, ly)
        pins_str += (
            f'    (pin {ptype} line (at {lx:.4f} {ly:.4f} 0) (length 2.54)\n'
            f'      (name "{pname}" (effects (font (size 1.016 1.016))))\n'
            f'      (number "{num}" (effects (font (size 1.016 1.016)))))\n'
        )
        num += 1

    for i, (pname, ptype) in enumerate(right_pins):
        ly = half - i * 2.54
        lx = +px
        pin_dict[pname] = (lx, ly)
        pins_str += (
            f'    (pin {ptype} line (at {lx:.4f} {ly:.4f} 180) (length 2.54)\n'
            f'      (name "{pname}" (effects (font (size 1.016 1.016))))\n'
            f'      (number "{num}" (effects (font (size 1.016 1.016)))))\n'
        )
        num += 1

    sym_text = (
        f'  (symbol "{name}"\n'
        f'    (pin_names (offset 0.254))\n'
        f'    (in_bom yes) (on_board yes)\n'
        f'    (property "Reference" "{ref_prefix}" (at 0 {body_h+2:.4f} 0)\n'
        f'      (effects (font (size 1.27 1.27))))\n'
        f'    (property "Value" "{name}" (at 0 {-(body_h+2):.4f} 0)\n'
        f'      (effects (font (size 1.27 1.27))))\n'
        f'    (symbol "{name}_0_1"\n'
        f'      (rectangle (start {-body_hw:.4f} {body_h:.4f})'
        f' (end {body_hw:.4f} {-body_h:.4f})\n'
        f'        (stroke (width 0.254) (type default))'
        f' (fill (type background))))\n'
        f'    (symbol "{name}_1_1"\n'
        f'{pins_str}'
        f'  ))'
    )
    return sym_text, pin_dict


def two_pin_sym(name, ptype='passive', length=2.54, vertical=True, ref_prefix='?'):
    """2-pin passive (R, C, SW_Push, Speaker)."""
    if vertical:
        # pin1 at top (local y=+len), pin2 at bottom (local y=-len)
        # stub angles: pin1 stub goes DOWN toward body (270), pin2 stub goes UP (90)
        p1 = (0,  length, 270)
        p2 = (0, -length,  90)
    else:
        # horizontal: pin1 left, pin2 right
        p1 = (-length, 0,   0)
        p2 = ( length, 0, 180)
    pin_dict = {'1': (p1[0], p1[1]), '2': (p2[0], p2[1])}
    sym_text = (
        f'  (symbol "{name}"\n'
        f'    (in_bom yes) (on_board yes)\n'
        f'    (property "Reference" "{ref_prefix}" (at 0 0 0)\n'
        f'      (effects (font (size 1.27 1.27))))\n'
        f'    (property "Value" "{name}" (at 0 0 0)\n'
        f'      (effects (font (size 1.27 1.27))))\n'
        f'    (symbol "{name}_0_1"\n'
        f'      (polyline (pts (xy -1.016 0) (xy 1.016 0))\n'
        f'        (stroke (width 0.254) (type default)) (fill (type none))))\n'
        f'    (symbol "{name}_1_1"\n'
        f'      (pin {ptype} line (at {p1[0]:.4f} {p1[1]:.4f} {p1[2]})'
        f' (length {length:.4f})\n'
        f'        (name "1" (effects (font (size 1.016 1.016))))\n'
        f'        (number "1" (effects (font (size 1.016 1.016)))))\n'
        f'      (pin {ptype} line (at {p2[0]:.4f} {p2[1]:.4f} {p2[2]})'
        f' (length {length:.4f})\n'
        f'        (name "2" (effects (font (size 1.016 1.016))))\n'
        f'        (number "2" (effects (font (size 1.016 1.016)))))\n'
        f'  ))'
    )
    return sym_text, pin_dict


def pot_sym():
    """3-pin potentiometer: pin1 top, pin2 bottom, pin3 wiper right."""
    pin_dict = {'1': (0, 3.81), '2': (0, -3.81), '3': (3.81, 0)}
    sym_text = (
        '  (symbol "POT"\n'
        '    (in_bom yes) (on_board yes)\n'
        '    (property "Reference" "RV" (at 0 0 0)\n'
        '      (effects (font (size 1.27 1.27))))\n'
        '    (property "Value" "POT" (at 0 0 0)\n'
        '      (effects (font (size 1.27 1.27))))\n'
        '    (symbol "POT_0_1"\n'
        '      (rectangle (start -1.016 2.54) (end 1.016 -2.54)\n'
        '        (stroke (width 0.254) (type default)) (fill (type none)))\n'
        '      (polyline (pts (xy 1.016 0) (xy 3.81 0))\n'
        '        (stroke (width 0.254) (type default)) (fill (type none)))\n'
        '      (polyline (pts (xy 2.54 1.27) (xy 3.81 0) (xy 2.54 -1.27))\n'
        '        (stroke (width 0.254) (type default)) (fill (type none))))\n'
        '    (symbol "POT_1_1"\n'
        '      (pin passive line (at 0 3.81 270) (length 1.27)\n'
        '        (name "1" (effects (font (size 1.016 1.016))))\n'
        '        (number "1" (effects (font (size 1.016 1.016)))))\n'
        '      (pin passive line (at 0 -3.81 90) (length 1.27)\n'
        '        (name "2" (effects (font (size 1.016 1.016))))\n'
        '        (number "2" (effects (font (size 1.016 1.016)))))\n'
        '      (pin passive line (at 3.81 0 180) (length 0)\n'
        '        (name "3" (effects (font (size 1.016 1.016))))\n'
        '        (number "3" (effects (font (size 1.016 1.016)))))\n'
        '  ))'
    )
    return sym_text, pin_dict


def conn4_sym():
    """4-pin single-row connector (all pins on left side of body)."""
    pin_dict = {str(i): (-5.08, 3.81 - (i-1)*2.54) for i in range(1, 5)}
    pins_str = ''
    for i in range(1, 5):
        ly = 3.81 - (i-1)*2.54
        pins_str += (
            f'      (pin passive line (at -5.08 {ly:.4f} 0) (length 2.54)\n'
            f'        (name "{i}" (effects (font (size 1.016 1.016))))\n'
            f'        (number "{i}" (effects (font (size 1.016 1.016)))))\n'
        )
    sym_text = (
        '  (symbol "Conn_01x04"\n'
        '    (in_bom yes) (on_board yes)\n'
        '    (property "Reference" "J" (at 0 6.35 0)\n'
        '      (effects (font (size 1.27 1.27))))\n'
        '    (property "Value" "Conn_01x04" (at 0 -6.35 0)\n'
        '      (effects (font (size 1.27 1.27))))\n'
        '    (symbol "Conn_01x04_0_1"\n'
        '      (rectangle (start -2.54 5.08) (end 2.54 -5.08)\n'
        '        (stroke (width 0.254) (type default)) (fill (type background))))\n'
        '    (symbol "Conn_01x04_1_1"\n'
        f'{pins_str}'
        '  ))'
    )
    return sym_text, pin_dict


def power_sym_def(name, is_vcc=True):
    """KiCad 9 power symbol definition. Uses bare (hide) boolean."""
    if is_vcc:
        body = (
            '      (polyline (pts (xy 0 0) (xy 0 1.27))\n'
            '        (stroke (width 0.254) (type default)) (fill (type none)))\n'
            '      (polyline (pts (xy -1.27 1.27) (xy 1.27 1.27))\n'
            '        (stroke (width 0.508) (type default)) (fill (type none)))\n'
        )
        pin_at = '0 0 270'   # pin at (0,0), stub goes down
        val_y  = 2.5
    else:
        body = (
            '      (polyline (pts (xy 0 0) (xy 0 -1.27))\n'
            '        (stroke (width 0.254) (type default)) (fill (type none)))\n'
            '      (polyline (pts (xy -1.27 -1.27) (xy 1.27 -1.27))\n'
            '        (stroke (width 0.508) (type default)) (fill (type none)))\n'
        )
        pin_at = '0 0 90'    # pin at (0,0), stub goes up
        val_y  = -2.5
    # KiCad 9: (hide) bare boolean replaces (hide yes)
    return (
        f'  (symbol "{name}"\n'
        f'    (power) (in_bom yes) (on_board yes)\n'
        f'    (property "Reference" "#PWR" (at 0 0 0)\n'
        f'      (effects (font (size 1.27 1.27)) (hide)))\n'
        f'    (property "Value" "{name}" (at 0 {val_y:.2f} 0)\n'
        f'      (effects (font (size 1.27 1.27))))\n'
        f'    (symbol "{name}_0_1"\n'
        f'{body}'
        f'    )\n'
        f'    (symbol "{name}_1_1"\n'
        f'      (pin power_in line (at {pin_at}) (length 0)\n'
        f'        (name "{name}" (effects (font (size 1.27 1.27))))\n'
        f'        (number "1" (effects (font (size 1.27 1.27)))))\n'
        f'  ))'
    )

# ─── Build all symbols ────────────────────────────────────────────────────────
# MSP430G2553 — 20-pin DIP (10 per side), LaunchPad pin ordering
msp430_left = [
    ('DVCC',      'power_in'),   # 1
    ('P1.0',      'bidirectional'),
    ('P1.1',      'bidirectional'),
    ('P1.2/PWM',  'bidirectional'),  # audio PWM
    ('P1.3/ADC',  'bidirectional'),  # ADC input
    ('P1.4',      'bidirectional'),
    ('P1.5/SCK',  'bidirectional'),  # SPI clock
    ('P2.0',      'bidirectional'),
    ('P2.1',      'bidirectional'),
    ('P2.2',      'bidirectional'),  # 10
]
msp430_right = [
    ('P2.3',      'bidirectional'),  # 11
    ('P2.4/SLD',  'bidirectional'),  # shift-reg SH/LD#
    ('P2.5',      'bidirectional'),
    ('P1.6/MISO', 'bidirectional'),  # SPI MISO
    ('P1.7/MOSI', 'bidirectional'),  # SPI MOSI
    ('TEST',      'input'),
    ('RST',       'input'),
    ('XIN',       'input'),
    ('DVSS',      'power_in'),
    ('DVSS2',     'power_in'),   # 20
]
msp430_sym, msp430_pd = ic_sym('MSP430G2553', msp430_left, msp430_right, ref_prefix='U')

# SN74HC165N — 16-pin DIP (8 per side), parallel-in/serial-out shift register
hc165_left = [
    ('SH_LD',    'input'),    # 1 — shift/load control
    ('CLK',      'input'),    # 2
    ('E',        'input'),    # 3 — parallel data
    ('F',        'input'),    # 4
    ('G',        'input'),    # 5
    ('H',        'input'),    # 6
    ('~QH~',     'output'),   # 7 — complementary serial out (NC)
    ('GND',      'power_in'), # 8
]
hc165_right = [
    ('VCC',      'power_in'), # 16
    ('CLK_INH',  'input'),    # 15 — clock inhibit (tie GND)
    ('D',        'input'),    # 14 — parallel data
    ('C',        'input'),    # 13
    ('B',        'input'),    # 12
    ('A',        'input'),    # 11
    ('SER',      'input'),    # 10 — serial in (NC, no daisy-chain)
    ('QH',       'output'),   # 9  — serial data out → MISO
]
hc165_sym, hc165_pd = ic_sym('SN74HC165N', hc165_left, hc165_right, ref_prefix='U')

# LM386N-1 — 8-pin DIP audio amp
lm386_left = [
    ('GAIN',     'passive'),   # 1
    ('IN-',      'input'),     # 2 — inverting in (to GND)
    ('GND',      'power_in'),  # 3
    ('VS',       'power_in'),  # 4 — positive supply (note: pin 4 bottom-left on DIP)
]
lm386_right = [
    ('GAIN8',    'passive'),   # 8 — optional 10µF/1.2kΩ between 1&8 for gain×200
    ('BYPASS',   'passive'),   # 7 — optional bypass cap
    ('OUTPUT',   'output'),    # 6
    ('NC_5',     'no_connect'),# 5 — VS in some datasheets; tie NC here
]
lm386_sym, lm386_pd = ic_sym('LM386N', lm386_left, lm386_right, body_hw=3.81, ref_prefix='U')

r_sym,   r_pd  = two_pin_sym('R',       'passive', vertical=True,  ref_prefix='R')
c_sym,   c_pd  = two_pin_sym('C',       'passive', vertical=True,  ref_prefix='C')
sw_sym,  sw_pd = two_pin_sym('SW_Push', 'passive', vertical=False, ref_prefix='SW')
spk_sym, spk_pd= two_pin_sym('Speaker', 'passive', vertical=False, ref_prefix='LS')

pot_sym_def, pot_pd   = pot_sym()
conn_sym_def, conn_pd = conn4_sym()
vcc_sym_def = power_sym_def('VCC', is_vcc=True)
gnd_sym_def = power_sym_def('GND', is_vcc=False)

# ─── Component positions (schematic world, mm) ────────────────────────────────
# Layout: left→right: buttons, U2(165), U1(MSP430), U3(LM386), Speaker
# Top row: OLED connector, LiPo connector
# Bottom row: Volume pot, ADC pot
# RC filter and decoupling cap between U1 and U3

U1  = (175, 125)   # MSP430G2553 — centre
U2  = (60,  125)   # SN74HC165N  — left of MSP430
U3  = (280, 125)   # LM386N-1    — right of MSP430
LS1 = (330, 125)   # Speaker
J1  = (60,   50)   # OLED SPI connector  — top left
J2  = (330,  50)   # LiPo charger connector — top right
RV1 = (60,  205)   # Volume pot  — bottom left
RV2 = (280, 205)   # ADC pot     — bottom right
R1  = (215, 158)   # 1kΩ RC filter resistor
C1  = (215, 173)   # 100nF RC filter cap
C2  = (148,  90)   # 100nF VCC decoupling cap on U1
BTN_X  = 20        # buttons X position
BTN_YS = [65, 75, 85, 95, 105, 115, 125, 135]   # 8 buttons, 10mm apart
RPU_X  = 42        # pull-up resistors X position

BTN_NETS = ['BTN_A','BTN_B','BTN_C','BTN_D','BTN_E','BTN_F','BTN_G','BTN_H']

def pin_w(comp, pd, pin_name):
    """Compute world coord for a named pin on a component."""
    cx, cy = comp
    lx, ly = pd[pin_name]
    return pw(cx, cy, lx, ly)

# ─── Place ICs ────────────────────────────────────────────────────────────────
place('MSP430G2553', U1[0], U1[1], 'U1', 'MSP430G2553')
place('SN74HC165N',  U2[0], U2[1], 'U2', 'SN74HC165N')
place('LM386N',      U3[0], U3[1], 'U3', 'LM386N-1')
place('Speaker',     LS1[0], LS1[1], 'LS1', 'SP-3605 8R')
place('Conn_01x04',  J1[0],  J1[1],  'J1', 'OLED_SPI')
place('Conn_01x04',  J2[0],  J2[1],  'J2', 'LiPo_Charger')
place('POT',         RV1[0], RV1[1], 'RV1', '10k')
place('POT',         RV2[0], RV2[1], 'RV2', '10k')
place('R',           R1[0],  R1[1],  'R1',  '1k')
place('C',           C1[0],  C1[1],  'C1',  '100nF')
place('C',           C2[0],  C2[1],  'C2',  '100nF')

for i, (by, bnet) in enumerate(zip(BTN_YS, BTN_NETS), 1):
    place('SW_Push', BTN_X, by, f'SW{i}', f'SW_{bnet}')
    place('R',       RPU_X, by, f'R{i+1}', '10k')

# ─── MSP430G2553 connections ──────────────────────────────────────────────────
pwr('VCC', *pin_w(U1, msp430_pd, 'DVCC'))
nc(        *pin_w(U1, msp430_pd, 'P1.0'))
nc(        *pin_w(U1, msp430_pd, 'P1.1'))
lbl('PWM_OUT', *pin_w(U1, msp430_pd, 'P1.2/PWM'), rot=180)
lbl('ADC_POT', *pin_w(U1, msp430_pd, 'P1.3/ADC'), rot=180)
nc(        *pin_w(U1, msp430_pd, 'P1.4'))
lbl('SCK', *pin_w(U1, msp430_pd, 'P1.5/SCK'), rot=180)
nc(        *pin_w(U1, msp430_pd, 'P2.0'))
nc(        *pin_w(U1, msp430_pd, 'P2.1'))
nc(        *pin_w(U1, msp430_pd, 'P2.2'))
# Right side
nc(          *pin_w(U1, msp430_pd, 'P2.3'))
lbl('SH_LD', *pin_w(U1, msp430_pd, 'P2.4/SLD'), rot=0)
nc(          *pin_w(U1, msp430_pd, 'P2.5'))
lbl('MISO',  *pin_w(U1, msp430_pd, 'P1.6/MISO'), rot=0)
lbl('MOSI',  *pin_w(U1, msp430_pd, 'P1.7/MOSI'), rot=0)
nc(          *pin_w(U1, msp430_pd, 'TEST'))
nc(          *pin_w(U1, msp430_pd, 'RST'))
nc(          *pin_w(U1, msp430_pd, 'XIN'))
pwr('GND',   *pin_w(U1, msp430_pd, 'DVSS'))
pwr('GND',   *pin_w(U1, msp430_pd, 'DVSS2'))

# ─── SN74HC165N connections ───────────────────────────────────────────────────
lbl('SH_LD',  *pin_w(U2, hc165_pd, 'SH_LD'), rot=180)
lbl('SCK',    *pin_w(U2, hc165_pd, 'CLK'),   rot=180)
lbl('BTN_E',  *pin_w(U2, hc165_pd, 'E'),     rot=180)
lbl('BTN_F',  *pin_w(U2, hc165_pd, 'F'),     rot=180)
lbl('BTN_G',  *pin_w(U2, hc165_pd, 'G'),     rot=180)
lbl('BTN_H',  *pin_w(U2, hc165_pd, 'H'),     rot=180)
nc(           *pin_w(U2, hc165_pd, '~QH~'))
pwr('GND',    *pin_w(U2, hc165_pd, 'GND'))
# Right side
pwr('VCC',    *pin_w(U2, hc165_pd, 'VCC'))
pwr('GND',    *pin_w(U2, hc165_pd, 'CLK_INH'))   # CLK_INH tied GND → no inhibit
lbl('BTN_D',  *pin_w(U2, hc165_pd, 'D'),    rot=0)
lbl('BTN_C',  *pin_w(U2, hc165_pd, 'C'),    rot=0)
lbl('BTN_B',  *pin_w(U2, hc165_pd, 'B'),    rot=0)
lbl('BTN_A',  *pin_w(U2, hc165_pd, 'A'),    rot=0)
nc(           *pin_w(U2, hc165_pd, 'SER'))
lbl('MISO',   *pin_w(U2, hc165_pd, 'QH'),   rot=0)

# ─── LM386N connections ────────────────────────────────────────────────────────
nc(               *pin_w(U3, lm386_pd, 'GAIN'))
lbl('AUDIO_IN',   *pin_w(U3, lm386_pd, 'IN-'),    rot=180)
pwr('GND',        *pin_w(U3, lm386_pd, 'GND'))
pwr('VCC',        *pin_w(U3, lm386_pd, 'VS'))
nc(               *pin_w(U3, lm386_pd, 'GAIN8'))
nc(               *pin_w(U3, lm386_pd, 'BYPASS'))
lbl('SPK_OUT',    *pin_w(U3, lm386_pd, 'OUTPUT'), rot=0)
nc(               *pin_w(U3, lm386_pd, 'NC_5'))

# ─── Speaker LS1 ──────────────────────────────────────────────────────────────
lbl('SPK_OUT',  *pin_w(LS1, spk_pd, '1'), rot=180)
pwr('GND',      *pin_w(LS1, spk_pd, '2'))

# ─── OLED connector J1 ────────────────────────────────────────────────────────
pwr('VCC',  *pin_w(J1, conn_pd, '1'))
pwr('GND',  *pin_w(J1, conn_pd, '2'))
lbl('SCK',  *pin_w(J1, conn_pd, '3'), rot=180)
lbl('MOSI', *pin_w(J1, conn_pd, '4'), rot=180)

# ─── LiPo charger J2 ──────────────────────────────────────────────────────────
pwr('VCC',     *pin_w(J2, conn_pd, '1'))
pwr('GND',     *pin_w(J2, conn_pd, '2'))
lbl('BAT_P',   *pin_w(J2, conn_pd, '3'), rot=180)
lbl('BAT_N',   *pin_w(J2, conn_pd, '4'), rot=180)

# ─── Volume pot RV1 ───────────────────────────────────────────────────────────
pwr('VCC',        *pin_w(RV1, pot_pd, '1'))
pwr('GND',        *pin_w(RV1, pot_pd, '2'))
lbl('VOL_WIPER',  *pin_w(RV1, pot_pd, '3'), rot=0)

# ─── ADC pot RV2 ──────────────────────────────────────────────────────────────
pwr('VCC',     *pin_w(RV2, pot_pd, '1'))
pwr('GND',     *pin_w(RV2, pot_pd, '2'))
lbl('ADC_POT', *pin_w(RV2, pot_pd, '3'), rot=0)

# ─── RC audio filter (R1 + C1) ────────────────────────────────────────────────
lbl('PWM_OUT',  *pin_w(R1, r_pd, '1'), rot=270)   # top of R1 (world y-3.81 above)
lbl('AUDIO_IN', *pin_w(R1, r_pd, '2'), rot=90)    # bottom of R1 → into C1/LM386
lbl('AUDIO_IN', *pin_w(C1, c_pd, '1'), rot=270)   # top of C1
pwr('GND',      *pin_w(C1, c_pd, '2'))             # bottom of C1 to GND

# ─── Decoupling cap C2 ────────────────────────────────────────────────────────
pwr('VCC', *pin_w(C2, c_pd, '1'))   # top of C2
pwr('GND', *pin_w(C2, c_pd, '2'))   # bottom of C2

# ─── 8 tactile buttons (SW1-SW8, horizontal, pin1=left/GND, pin2=right/BTN) ──
for i, (by, bnet) in enumerate(zip(BTN_YS, BTN_NETS), 1):
    pwr('GND', *pin_w((BTN_X, by), sw_pd, '1'))
    lbl(bnet,  *pin_w((BTN_X, by), sw_pd, '2'), rot=0)

# ─── 8 pull-up resistors (R2-R9, vertical, pin1=top/VCC, pin2=bottom/BTN) ────
for i, (by, bnet) in enumerate(zip(BTN_YS, BTN_NETS), 2):
    pwr('VCC',  *pin_w((RPU_X, by), r_pd, '1'))   # pin1 world y = cy-3.81 (above)
    lbl(bnet,   *pin_w((RPU_X, by), r_pd, '2'), rot=90)  # pin2 world y = cy+3.81

# ─── Assemble lib_symbols block ────────────────────────────────────────────────
lib_block = '\n'.join([
    msp430_sym, hc165_sym, lm386_sym,
    r_sym, c_sym, sw_sym, spk_sym,
    pot_sym_def, conn_sym_def,
    vcc_sym_def, gnd_sym_def,
])

# ─── Assemble all schematic elements ─────────────────────────────────────────
all_elements = '\n'.join(
    f'  {e}' for e in (PLACED + WIRES + LABELS + POWERS + NC)
)

# ─── Build full schematic ─────────────────────────────────────────────────────
SCHEMATIC_UUID = uid()
sch = f"""(kicad_sch
  (version 20250114)
  (generator "eeschema")
  (generator_version "9.0")
  (uuid "{SCHEMATIC_UUID}")
  (paper "B")
  (title_block
    (title "MSP430G2553 Game Boy")
    (date "2026-03-01")
    (rev "3.0")
    (company "")
    (comment 1 "MCU: MSP430G2553 (LaunchPad MSP-EXP430G2)")
    (comment 2 "SPI: P1.5=SCK  P1.6=MISO(QH serial out)  P1.7=MOSI  P2.4=SH/LD#")
    (comment 3 "Audio: P1.2-PWM -> 1k+100nF -> LM386N-IN- -> OUTPUT -> 8ohm speaker")
    (comment 4 "Buttons: SN74HC165N parallel-in serial-out, 10k pull-ups, BTN_A..H")
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

# ─── Validate ─────────────────────────────────────────────────────────────────
opens  = sch.count('(')
closes = sch.count(')')
assert opens == closes, f"PAREN MISMATCH: {opens} open vs {closes} close"

OUT = '/sessions/kind-loving-bardeen/mnt/outputs/msp430_gameboy.kicad_sch'
with open(OUT, 'w') as f:
    f.write(sch)

import os
print(f"Written: {os.path.getsize(OUT):,} bytes, {sch.count(chr(10))} lines")
print(f"Parens: {opens} open = {closes} close ✓")
print(f"Placed: {len(PLACED)}  Wires: {len(WIRES)}  Labels: {len(LABELS)}"
      f"  Powers: {len(POWERS)}  NC: {len(NC)}")

# kiutils validation
try:
    from kiutils.schematic import Schematic
    s = Schematic().from_file(OUT)
    print(f"kiutils: libSymbols={len(s.libSymbols)}"
          f"  symbols={len(s.schematicSymbols)}"
          f"  labels={len(s.labels)}"
          f"  noConnects={len(s.noConnects)}")
except Exception as e:
    print(f"kiutils warning: {e}")

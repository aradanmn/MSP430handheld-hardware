"""
gen_kicad7.py — MSP430G2553 Game Boy schematic generator
Target: KiCad 9.0.7 native format (version 20250114)

ROOT CAUSE OF PRIOR "NOTHING CONNECTED" BUG:
  Component positions (175, 125, 60, 280, …) were NOT multiples of 2.54 mm.
  KiCad's schematic grid is 50 mil = 1.27 mm (fine) / 100 mil = 2.54 mm (coarse).
  Off-grid pin endpoints cause wire stubs to miss pins → dangling wires → ERC errors.

KEY FIX in gen_kicad7.py:
  ALL cx, cy are exact multiples of G = 2.54 mm.
  Pin endpoint x = cx ± 3G = cx ± 7.62 mm → also multiple of G. ✓
  Pin endpoint y = cy ± n×1.27 mm → on 1.27 mm grid (cy is multiple of G = 2×1.27). ✓
  Wire stubs ±G from pin endpoint → on G grid. ✓

Coordinate system:
  Symbol local:   Y increases UP  (math convention)
  Schematic world: Y increases DOWN (screen convention)
  Mapping: world = (cx + lx,  cy - ly)    [Y negated]
"""
import uuid as _uuid

G = 2.54   # 1 grid unit = 100 mil

def uid():
    return str(_uuid.uuid4())

# ─── Coordinate helpers ───────────────────────────────────────────────────────
def pw(cx, cy, lx, ly):
    """World coords for pin at symbol-local (lx, ly), component at (cx, cy)."""
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

STUB = G   # wire stub length = 1 grid unit = 2.54 mm

def lbl(net, px, py, rot=0):
    """Label with stub wire. Pin endpoint at (px,py); stub extends outward."""
    if   rot == 0:   ex, ey = px + STUB, py
    elif rot == 180: ex, ey = px - STUB, py
    elif rot == 90:  ex, ey = px, py + STUB
    elif rot == 270: ex, ey = px, py - STUB
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
def ic_sym(name, left_pins, right_pins, body_hw=2*G, ref_prefix='U'):
    """
    Build a KiCad 9 lib symbol for a generic IC.
    body_hw MUST be a multiple of G (=2.54) for X pin endpoints to land on grid.
    Pin pitch = 2.54 mm. Pin endpoint offset = body_hw + G from IC centre.
    """
    n_left  = len(left_pins)
    n_right = len(right_pins)
    n = max(n_left, n_right)
    half = (n - 1) * 1.27          # ± half-span; pin pitch = 2.54 mm
    body_h = half + 1.27
    px = body_hw + G               # pin endpoint offset from centre

    pin_dict = {}
    pins_str = ''
    num = 1

    for i, (pname, ptype) in enumerate(left_pins):
        ly = half - i * 2.54
        lx = -px
        pin_dict[pname] = (lx, ly)
        pins_str += (
            f'    (pin {ptype} line (at {lx:.4f} {ly:.4f} 0) (length {G:.4f})\n'
            f'      (name "{pname}" (effects (font (size 1.016 1.016))))\n'
            f'      (number "{num}" (effects (font (size 1.016 1.016)))))\n'
        )
        num += 1

    for i, (pname, ptype) in enumerate(right_pins):
        ly = half - i * 2.54
        lx = +px
        pin_dict[pname] = (lx, ly)
        pins_str += (
            f'    (pin {ptype} line (at {lx:.4f} {ly:.4f} 180) (length {G:.4f})\n'
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


def two_pin_sym(name, ptype='passive', length=G, vertical=True, ref_prefix='?'):
    """2-pin passive. Pins at ±length from centre. All coords multiples of G."""
    if vertical:
        p1 = (0,  length, 270)   # top pin, stub goes up (away from body)
        p2 = (0, -length,  90)   # bottom pin, stub goes down
    else:
        p1 = (-length, 0,   0)   # left pin
        p2 = ( length, 0, 180)   # right pin
    pin_dict = {'1': (p1[0], p1[1]), '2': (p2[0], p2[1])}
    sym_text = (
        f'  (symbol "{name}"\n'
        f'    (in_bom yes) (on_board yes)\n'
        f'    (property "Reference" "{ref_prefix}" (at 0 0 0)\n'
        f'      (effects (font (size 1.27 1.27))))\n'
        f'    (property "Value" "{name}" (at 0 0 0)\n'
        f'      (effects (font (size 1.27 1.27))))\n'
        f'    (symbol "{name}_0_1"\n'
        f'      (polyline (pts (xy {-0.4*G:.4f} 0) (xy {0.4*G:.4f} 0))\n'
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
    """3-pin potentiometer. Pins at ±3G (top/bottom) and +3G (wiper right).
    3G = 7.62 mm = 3×2.54 mm → on 2.54 mm grid. ✓"""
    L = 3 * G   # 7.62 mm — pin endpoint offset
    pin_dict = {'1': (0, L), '2': (0, -L), '3': (L, 0)}
    HL = 2 * G  # half-length of resistive element body = 5.08 mm
    sym_text = (
        '  (symbol "POT"\n'
        '    (in_bom yes) (on_board yes)\n'
        '    (property "Reference" "RV" (at 0 0 0)\n'
        '      (effects (font (size 1.27 1.27))))\n'
        '    (property "Value" "POT" (at 0 0 0)\n'
        '      (effects (font (size 1.27 1.27))))\n'
        '    (symbol "POT_0_1"\n'
        f'      (rectangle (start {-G:.4f} {HL:.4f}) (end {G:.4f} {-HL:.4f})\n'
        '        (stroke (width 0.254) (type default)) (fill (type none)))\n'
        f'      (polyline (pts (xy {G:.4f} 0) (xy {L:.4f} 0))\n'
        '        (stroke (width 0.254) (type default)) (fill (type none)))\n'
        f'      (polyline (pts (xy {2*G:.4f} {G:.4f}) (xy {L:.4f} 0) (xy {2*G:.4f} {-G:.4f}))\n'
        '        (stroke (width 0.254) (type default)) (fill (type none))))\n'
        '    (symbol "POT_1_1"\n'
        f'      (pin passive line (at 0 {L:.4f} 270) (length {G:.4f})\n'
        '        (name "1" (effects (font (size 1.016 1.016))))\n'
        '        (number "1" (effects (font (size 1.016 1.016)))))\n'
        f'      (pin passive line (at 0 {-L:.4f} 90) (length {G:.4f})\n'
        '        (name "2" (effects (font (size 1.016 1.016))))\n'
        '        (number "2" (effects (font (size 1.016 1.016)))))\n'
        f'      (pin passive line (at {L:.4f} 0 180) (length 0)\n'
        '        (name "3" (effects (font (size 1.016 1.016))))\n'
        '        (number "3" (effects (font (size 1.016 1.016)))))\n'
        '  ))'
    )
    return sym_text, pin_dict


def conn4_sym():
    """4-pin single-row connector. All pins on left side. Pitch = G = 2.54 mm."""
    half = 1.5 * G   # = 3.81 mm for 4 pins centred
    # pins at y = +3G/2, +G/2, -G/2, -3G/2  → multiples of 0.5G = 1.27 mm ✓
    pin_ys = [half - i * G for i in range(4)]   # [3.81, 1.27, -1.27, -3.81]
    pin_dict = {str(i+1): (-2*G, pin_ys[i]) for i in range(4)}
    pins_str = ''
    for i in range(4):
        ly = pin_ys[i]
        pins_str += (
            f'      (pin passive line (at {-2*G:.4f} {ly:.4f} 0) (length {G:.4f})\n'
            f'        (name "{i+1}" (effects (font (size 1.016 1.016))))\n'
            f'        (number "{i+1}" (effects (font (size 1.016 1.016)))))\n'
        )
    sym_text = (
        '  (symbol "Conn_01x04"\n'
        '    (in_bom yes) (on_board yes)\n'
        f'    (property "Reference" "J" (at 0 {2*G+1:.4f} 0)\n'
        '      (effects (font (size 1.27 1.27))))\n'
        f'    (property "Value" "Conn_01x04" (at 0 {-(2*G+1):.4f} 0)\n'
        '      (effects (font (size 1.27 1.27))))\n'
        '    (symbol "Conn_01x04_0_1"\n'
        f'      (rectangle (start {-G:.4f} {2*G:.4f}) (end {G:.4f} {-2*G:.4f})\n'
        '        (stroke (width 0.254) (type default)) (fill (type background))))\n'
        '    (symbol "Conn_01x04_1_1"\n'
        f'{pins_str}'
        '  ))'
    )
    return sym_text, pin_dict


def power_sym_def(name, is_vcc=True):
    """KiCad 9 power symbol. Bare (hide) boolean (not (hide yes))."""
    if is_vcc:
        body = (
            f'      (polyline (pts (xy 0 0) (xy 0 {G:.4f}))\n'
            '        (stroke (width 0.254) (type default)) (fill (type none)))\n'
            f'      (polyline (pts (xy {-G:.4f} {G:.4f}) (xy {G:.4f} {G:.4f}))\n'
            '        (stroke (width 0.508) (type default)) (fill (type none)))\n'
        )
        pin_at = f'0 0 270'
        val_y  =  2.5
    else:
        body = (
            f'      (polyline (pts (xy 0 0) (xy 0 {-G:.4f}))\n'
            '        (stroke (width 0.254) (type default)) (fill (type none)))\n'
            f'      (polyline (pts (xy {-G:.4f} {-G:.4f}) (xy {G:.4f} {-G:.4f}))\n'
            '        (stroke (width 0.508) (type default)) (fill (type none)))\n'
        )
        pin_at = f'0 0 90'
        val_y  = -2.5
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
# MSP430G2553 — 20-pin DIP (10 per side)
msp430_left = [
    ('DVCC',      'power_in'),
    ('P1.0',      'bidirectional'),
    ('P1.1',      'bidirectional'),
    ('P1.2/PWM',  'bidirectional'),
    ('P1.3/ADC',  'bidirectional'),
    ('P1.4',      'bidirectional'),
    ('P1.5/SCK',  'bidirectional'),
    ('P2.0',      'bidirectional'),
    ('P2.1',      'bidirectional'),
    ('P2.2',      'bidirectional'),
]
msp430_right = [
    ('P2.3',      'bidirectional'),
    ('P2.4/SLD',  'bidirectional'),
    ('P2.5',      'bidirectional'),
    ('P1.6/MISO', 'bidirectional'),
    ('P1.7/MOSI', 'bidirectional'),
    ('TEST',      'input'),
    ('RST',       'input'),
    ('XIN',       'input'),
    ('DVSS',      'power_in'),
    ('DVSS2',     'power_in'),
]
msp430_sym, msp430_pd = ic_sym('MSP430G2553', msp430_left, msp430_right, body_hw=2*G, ref_prefix='U')

# SN74HC165N — 16-pin DIP (8 per side)
hc165_left = [
    ('SH_LD',   'input'),
    ('CLK',     'input'),
    ('E',       'input'),
    ('F',       'input'),
    ('G',       'input'),
    ('H',       'input'),
    ('~QH~',    'output'),
    ('GND',     'power_in'),
]
hc165_right = [
    ('VCC',     'power_in'),
    ('CLK_INH', 'input'),
    ('D',       'input'),
    ('C',       'input'),
    ('B',       'input'),
    ('A',       'input'),
    ('SER',     'input'),
    ('QH',      'output'),
]
hc165_sym, hc165_pd = ic_sym('SN74HC165N', hc165_left, hc165_right, body_hw=2*G, ref_prefix='U')

# LM386N-1 — 8-pin DIP audio amp
# body_hw=2G (was 3.81) ensures X pin endpoints on 2.54mm grid
lm386_left = [
    ('GAIN',  'passive'),
    ('IN-',   'input'),
    ('GND',   'power_in'),
    ('VS',    'power_in'),
]
lm386_right = [
    ('GAIN8', 'passive'),
    ('BYPASS','passive'),
    ('OUTPUT','output'),
    ('NC_5',  'no_connect'),
]
lm386_sym, lm386_pd = ic_sym('LM386N', lm386_left, lm386_right, body_hw=2*G, ref_prefix='U')

r_sym,    r_pd   = two_pin_sym('R',       'passive', length=G, vertical=True,  ref_prefix='R')
c_sym,    c_pd   = two_pin_sym('C',       'passive', length=G, vertical=True,  ref_prefix='C')
sw_sym,   sw_pd  = two_pin_sym('SW_Push', 'passive', length=G, vertical=False, ref_prefix='SW')
spk_sym,  spk_pd = two_pin_sym('Speaker', 'passive', length=G, vertical=False, ref_prefix='LS')

pot_sym_def,  pot_pd   = pot_sym()
conn_sym_def, conn_pd  = conn4_sym()
vcc_sym_def = power_sym_def('VCC', is_vcc=True)
gnd_sym_def = power_sym_def('GND', is_vcc=False)

# ─── Component positions — ALL multiples of G = 2.54 mm ───────────────────────
# Grid layout (units of G):
#   Col A (X≈8G)  : buttons
#   Col B (X≈17G) : pull-up resistors
#   Col C (X≈24G) : U2 SN74HC165N, J1 OLED, RV1 vol
#   Col D (X≈69G) : U1 MSP430, C2 decoupling
#   Col E (X≈84G) : R1, C1 RC filter
#   Col F (X≈110G): U3 LM386, RV2 ADC
#   Col G (X≈130G): LS1 Speaker, J2 LiPo

U1  = (69*G,  49*G)   # MSP430G2553
U2  = (24*G,  49*G)   # SN74HC165N
U3  = (110*G, 49*G)   # LM386N
LS1 = (130*G, 49*G)   # Speaker
J1  = (24*G,  20*G)   # OLED SPI connector
J2  = (130*G, 20*G)   # LiPo charger connector
RV1 = (24*G,  80*G)   # Volume pot
RV2 = (110*G, 80*G)   # ADC pot
R1  = (84*G,  62*G)   # 1k RC filter resistor
C1  = (84*G,  68*G)   # 100nF RC filter cap
C2  = (58*G,  36*G)   # 100nF VCC decoupling

BTN_X  = 8*G                                  # buttons X
RPU_X  = 17*G                                 # pull-up resistors X
# 8 button rows, spaced 4G = 10.16 mm apart, centred near U2's Y
BTN_YS = [n*G for n in [36, 40, 44, 48, 52, 56, 60, 64]]

BTN_NETS = ['BTN_A','BTN_B','BTN_C','BTN_D','BTN_E','BTN_F','BTN_G','BTN_H']

# ─── Verify all positions on G grid ──────────────────────────────────────────
def check_grid(name, val, unit=G):
    r = val % unit
    if r > 1e-9 and (unit - r) > 1e-9:
        print(f"  WARN: {name}={val:.4f} not on {unit:.4f}mm grid (rem={r:.6f})")

for label, pt in [('U1',U1),('U2',U2),('U3',U3),('LS1',LS1),
                   ('J1',J1),('J2',J2),('RV1',RV1),('RV2',RV2),
                   ('R1',R1),('C1',C1),('C2',C2)]:
    check_grid(f'{label}.x', pt[0])
    check_grid(f'{label}.y', pt[1])
check_grid('BTN_X', BTN_X)
check_grid('RPU_X', RPU_X)
for i, y in enumerate(BTN_YS):
    check_grid(f'BTN_Y[{i}]', y)
print("Grid check done.")

def pin_w(comp, pd, pin_name):
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

# ─── SN74HC165N connections ────────────────────────────────────────────────────
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
pwr('GND',    *pin_w(U2, hc165_pd, 'CLK_INH'))
lbl('BTN_D',  *pin_w(U2, hc165_pd, 'D'),    rot=0)
lbl('BTN_C',  *pin_w(U2, hc165_pd, 'C'),    rot=0)
lbl('BTN_B',  *pin_w(U2, hc165_pd, 'B'),    rot=0)
lbl('BTN_A',  *pin_w(U2, hc165_pd, 'A'),    rot=0)
nc(           *pin_w(U2, hc165_pd, 'SER'))
lbl('MISO',   *pin_w(U2, hc165_pd, 'QH'),   rot=0)

# ─── LM386N connections ────────────────────────────────────────────────────────
nc(              *pin_w(U3, lm386_pd, 'GAIN'))
lbl('AUDIO_IN',  *pin_w(U3, lm386_pd, 'IN-'),    rot=180)
pwr('GND',       *pin_w(U3, lm386_pd, 'GND'))
pwr('VCC',       *pin_w(U3, lm386_pd, 'VS'))
nc(              *pin_w(U3, lm386_pd, 'GAIN8'))
nc(              *pin_w(U3, lm386_pd, 'BYPASS'))
lbl('SPK_OUT',   *pin_w(U3, lm386_pd, 'OUTPUT'), rot=0)
nc(              *pin_w(U3, lm386_pd, 'NC_5'))

# ─── Speaker LS1 ──────────────────────────────────────────────────────────────
lbl('SPK_OUT', *pin_w(LS1, spk_pd, '1'), rot=180)
pwr('GND',     *pin_w(LS1, spk_pd, '2'))

# ─── OLED connector J1 ────────────────────────────────────────────────────────
pwr('VCC',  *pin_w(J1, conn_pd, '1'))
pwr('GND',  *pin_w(J1, conn_pd, '2'))
lbl('SCK',  *pin_w(J1, conn_pd, '3'), rot=180)
lbl('MOSI', *pin_w(J1, conn_pd, '4'), rot=180)

# ─── LiPo charger J2 ──────────────────────────────────────────────────────────
pwr('VCC',   *pin_w(J2, conn_pd, '1'))
pwr('GND',   *pin_w(J2, conn_pd, '2'))
lbl('BAT_P', *pin_w(J2, conn_pd, '3'), rot=180)
lbl('BAT_N', *pin_w(J2, conn_pd, '4'), rot=180)

# ─── Volume pot RV1 ───────────────────────────────────────────────────────────
pwr('VCC',       *pin_w(RV1, pot_pd, '1'))
pwr('GND',       *pin_w(RV1, pot_pd, '2'))
lbl('VOL_WIPER', *pin_w(RV1, pot_pd, '3'), rot=0)

# ─── ADC pot RV2 ──────────────────────────────────────────────────────────────
pwr('VCC',     *pin_w(RV2, pot_pd, '1'))
pwr('GND',     *pin_w(RV2, pot_pd, '2'))
lbl('ADC_POT', *pin_w(RV2, pot_pd, '3'), rot=0)

# ─── RC audio filter R1 + C1 ─────────────────────────────────────────────────
lbl('PWM_OUT',  *pin_w(R1, r_pd, '1'), rot=270)   # top of R1
lbl('AUDIO_IN', *pin_w(R1, r_pd, '2'), rot=90)    # bottom of R1
lbl('AUDIO_IN', *pin_w(C1, c_pd, '1'), rot=270)   # top of C1
pwr('GND',      *pin_w(C1, c_pd, '2'))             # bottom of C1

# ─── Decoupling cap C2 ────────────────────────────────────────────────────────
pwr('VCC', *pin_w(C2, c_pd, '1'))
pwr('GND', *pin_w(C2, c_pd, '2'))

# ─── 8 tactile buttons SW1-SW8 (horizontal) ───────────────────────────────────
for i, (by, bnet) in enumerate(zip(BTN_YS, BTN_NETS), 1):
    pwr('GND', *pin_w((BTN_X, by), sw_pd, '1'))
    lbl(bnet,  *pin_w((BTN_X, by), sw_pd, '2'), rot=0)

# ─── 8 pull-up resistors R2-R9 (vertical) ────────────────────────────────────
for i, (by, bnet) in enumerate(zip(BTN_YS, BTN_NETS), 2):
    pwr('VCC', *pin_w((RPU_X, by), r_pd, '1'))
    lbl(bnet,  *pin_w((RPU_X, by), r_pd, '2'), rot=90)

# ─── Assemble lib_symbols block ──────────────────────────────────────────────
lib_block = '\n'.join([
    msp430_sym, hc165_sym, lm386_sym,
    r_sym, c_sym, sw_sym, spk_sym,
    pot_sym_def, conn_sym_def,
    vcc_sym_def, gnd_sym_def,
])

# ─── Assemble schematic elements ─────────────────────────────────────────────
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
    (rev "4.0")
    (company "")
    (comment 1 "MCU: MSP430G2553 (LaunchPad MSP-EXP430G2)")
    (comment 2 "SPI: P1.5=SCK  P1.6=MISO  P1.7=MOSI  P2.4=SH/LD#")
    (comment 3 "Audio: P1.2-PWM -> 1k+100nF -> LM386N-IN- -> OUTPUT -> 8ohm speaker")
    (comment 4 "Buttons: SN74HC165N parallel-in/serial-out, 10k pull-ups, BTN_A..H")
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

# ─── Validate ────────────────────────────────────────────────────────────────
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

# ─── KiCad 9 format audit ────────────────────────────────────────────────────
checks = [
    ('Version 20250114',      '(version 20250114)' in sch),
    ('generator_version 9.0', '"9.0"' in sch),
    ('exclude_from_sim',      'exclude_from_sim' in sch),
    ('dnp field',             '(dnp no)' in sch),
    ('No hide yes',           '(hide yes)' not in sch),
    ('Bare (hide) boolean',   '(hide))' in sch),
    ('fields_autoplaced',     'fields_autoplaced' in sch),
    ('Single kicad_sch',      sch.count('(kicad_sch') == 1),
    ('lib_symbols present',   '(lib_symbols' in sch),
    ('sheet_instances',       'sheet_instances' in sch),
    ('No sheets block',       '(sheets' not in sch),
    ('Wire stubs present',    len(WIRES) > 0),
]
print("\nKiCad 9 format audit:")
all_ok = True
for desc, result in checks:
    status = '✓' if result else '✗ FAIL'
    print(f"  {status}  {desc}")
    if not result:
        all_ok = False
print(f"\nRESULT: {'ALL CHECKS PASS ✓' if all_ok else 'SOME CHECKS FAILED ✗'}")

# ─── kiutils validation ───────────────────────────────────────────────────────
try:
    from kiutils.schematic import Schematic
    s = Schematic().from_file(OUT)
    print(f"kiutils: libSymbols={len(s.libSymbols)}"
          f"  symbols={len(s.schematicSymbols)}"
          f"  labels={len(s.labels)}"
          f"  noConnects={len(s.noConnects)}")
except Exception as e:
    print(f"kiutils: {e}")

# ─── Spot-check pin endpoint grid alignment ───────────────────────────────────
print("\nPin endpoint grid check (sample):")
for comp_name, comp, pd in [('U1', U1, msp430_pd), ('U2', U2, hc165_pd)]:
    for pname in list(pd.keys())[:3]:
        wx, wy = pin_w(comp, pd, pname)
        ok_x = abs((wx % 1.27)) < 1e-6 or abs((wx % 1.27) - 1.27) < 1e-6
        ok_y = abs((wy % 1.27)) < 1e-6 or abs((wy % 1.27) - 1.27) < 1e-6
        print(f"  {comp_name}.{pname}: ({wx:.4f}, {wy:.4f}) "
              f"x={'✓' if ok_x else '✗'} y={'✓' if ok_y else '✗'}")

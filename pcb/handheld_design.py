"""
handheld_design.py -- single source of truth for the MSP430 handheld carrier board.

Pure data, no KiCad imports. Consumed by gen_pcb.py (which runs inside KiCad's
Python) to build the board, the netlist report and enclosure/board_params.scad.

Coordinates: millimetres, board FRONT view (the side the player looks at),
origin at the top-left corner of the PCB, x right, y down. Parts on the back
are still positioned in front-view coordinates; the generator mirrors them.

The MCU is NOT on this board. A TI LaunchPad (MSP-EXP430G2ET) plugs onto the
back, BoosterPack-style, through the two 1x10 sockets J5/J6.
"""

BOARD_W, BOARD_H, BOARD_R = 90.0, 140.0, 3.0
REV = "A"

L = "/usr/share/kicad/footprints/"          # stock KiCad 9 library (inside the container)

# ── Mechanical features shared with the enclosure ────────────────────────────
CASE_SCREWS = [(4, 4), (86, 4), (4, 77), (86, 77), (4, 136), (86, 136)]   # M3

# Adafruit #2674 OLED module, top view, origin = module top-left corner.
# Outline 85 x 58 from Adafruit; hole/header/bezel offsets scaled from Adafruit's
# product photos (+-0.5 mm) -- MEASURE the real module before ordering boards.
OLED = dict(
    w=85.0, h=58.0, at=(2.5, 9.0),
    hdr_x0=18.37, hdr_y=1.6, hdr_n=20,                 # pin 1 on the left, front view
    holes=[(2.5, 2.5), (82.5, 2.5), (2.5, 55.5), (82.5, 55.5)],
    bezel=(5.5, 8.5, 74.0, 46.0),                      # x, y, w, h on the module
    gap=11.04,                                         # 8.5 socket + 2.54 header plastic
    pcb_t=1.4, bezel_h=5.0,
)

BATTERY = dict(x=27.0, y=12.5, w=36.0, h=60.0, t=7.0)      # Adafruit #2011, in the bay under the OLED
SPEAKER = dict(x=66.0, y=103.0, d=40.0, t=6.5)             # behind the board, fixed to the back shell
LAUNCHPAD = dict(cx=45.0, pin1_y=34.0, row_pitch=45.72,    # BoosterPack standard: rows 1.8" apart
                 w=51.0, usb_edge_to_pin1=30.0, length=69.0,   # ASSUMED outline -- measure
                 gap=11.04)

BUTTONS = {            # name: (x, y, cap style)
    "UP": (21, 91, "dpad"), "DOWN": (21, 111, "dpad"),
    "LEFT": (11, 101, "dpad"), "RIGHT": (31, 101, "dpad"),
    "SELECT": (37, 127, "pill"), "START": (53, 127, "pill"),
    "B": (63, 105, "ab"), "A": (77, 95, "ab"),
}
VOLUME = (45.0, 84.0)      # pot shaft axis
LED = (12.0, 72.5)
PWR_SWITCH = (71.0, 131.0)  # on the back; slides along x

# ── Carrier-module footprints (generated into lib/handheld.pretty) ───────────
# Pads: (number, name, x, y). Geometry for the two Adafruit boards is taken from
# Adafruit's published Eagle .brd files (y flipped to KiCad's y-down).
MODULES = {
    "Adafruit_2674_OLED_2.7in": dict(
        w=OLED["w"], h=OLED["h"], drill=1.0, pad=1.7,
        pads=[(str(i + 1), n, OLED["hdr_x0"] + 2.54 * i, OLED["hdr_y"]) for i, n in enumerate(
            ["GND", "3V3", "", "DC", "", "", "CLK", "DIN", "", "", "", "", "", "", "CS", "RST", "", "", "", "FG"])],
        npth=[(x, y, 2.7) for x, y in OLED["holes"]],
        fab=[OLED["bezel"]], label="OLED #2674 (socket, M2.5x11 standoffs)", silk_names=False,
        courtyard=False),   # sits 11 mm up; parts live underneath it
    "Adafruit_4410_USBC_MicroLipo": dict(
        w=22.86, h=19.05, drill=1.0, pad=1.7,
        pads=[("1", "5V", 6.35, 2.54), ("2", "D-", 8.89, 2.54), ("3", "D+", 11.43, 2.54),
              ("4", "GND", 13.97, 2.54), ("5", "BAT", 16.51, 2.54)],
        npth=[(2.54, 16.51, 2.7), (20.32, 16.51, 2.7)],
        fab=[(-1.2, 5.0, 7.5, 9.05)], label="#4410 USB-C", silk_names=True),
    "Adafruit_1903_PowerBoost500": dict(
        w=27.94, h=21.59, drill=1.0, pad=1.7,
        pads=[("1", "BAT", 7.62, 1.27), ("2", "GND", 10.16, 1.27), ("3", "EN", 12.70, 1.27),
              ("4", "LBO", 15.24, 1.27), ("5", "GND", 17.78, 1.27), ("6", "5V", 20.32, 1.27)],
        npth=[(2.54, 19.05, 2.7)],
        fab=[], label="#1903 PowerBoost", silk_names=True),
    # Pin ORDER along the row is not verified against the part: the silkscreen
    # names each hole; if the Pololu board's own labels run the other way, mount
    # it component-side-down (same footprint, same body position).
    "Pololu_S7V8F3": dict(
        w=11.43, h=16.51, drill=1.0, pad=1.7,
        pads=[("1", "SHDN", 1.905, 1.27), ("2", "VIN", 4.445, 1.27),
              ("3", "GND", 6.985, 1.27), ("4", "VOUT", 9.525, 1.27)],
        npth=[], fab=[], label="S7V8F3", silk_names=True),
    "SW_E-Switch_EG1218": dict(
        w=11.6, h=4.0, drill=1.0, pad=1.7, origin=(5.8, 2.0),
        pads=[("1", "", 3.3, 2.0), ("2", "", 5.8, 2.0), ("3", "", 8.3, 2.0)],
        npth=[], fab=[], label="", silk_names=False),
}

# ── Parts ────────────────────────────────────────────────────────────────────
# (ref, footprint, value, x, y, rot, side, anchor, {pad: net})
# anchor: "pads" = centre of the pad bounding box sits at (x, y)
#         "origin" = footprint origin sits at (x, y)
#         (dx, dy) = that footprint-local point sits at (x, y)
H = "handheld:"
DIP8 = "Package_DIP:DIP-8_W7.62mm"
R = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"
C = "Capacitor_THT:C_Disc_D3.0mm_W1.6mm_P2.50mm"
CP5 = "Capacitor_THT:CP_Radial_D5.0mm_P2.00mm"
CP6 = "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm"
SW = "Button_Switch_THT:SW_TH_Tactile_Omron_B3F-100x"
SOCK10 = "Connector_PinSocket_2.54mm:PinSocket_1x10_P2.54mm_Vertical"

LP = LAUNCHPAD
LPY = LP["pin1_y"] + 4.5 * 2.54
BTN_NET = {"UP": "BTN_UP", "DOWN": "BTN_DOWN", "LEFT": "BTN_LEFT", "RIGHT": "BTN_RIGHT",
           "SELECT": "BTN_SELECT", "START": "BTN_START", "B": "BTN_B", "A": "BTN_A"}

def _btn(i, name):
    x, y, _ = BUTTONS[name]
    return (f"SW{i}", SW, name, x, y, 0, "F", "pads", {"1": BTN_NET[name], "2": "GND"})

def _pullup(ref, net, x, y, rot=0, side="F", val="10k"):
    return (ref, R, val, x, y, rot, side, "pads", {"1": "+3V3", "2": net})

PARTS = [
    # ── display ──
    ("A1", H + "Adafruit_2674_OLED_2.7in", "OLED 128x64 SSD1325", *OLED["at"], 0, "F", "origin",
     {"1": "GND", "2": "+3V3", "4": "OLED_DC", "7": "SCK", "8": "MOSI",
      "15": "OLED_CS", "16": "OLED_RST", "20": "GND"}),
    # ── LaunchPad sockets (back). Front view shows the LaunchPad's top side
    #    un-mirrored: J1 (pins 1-10) on the left, J2 (pins 20-11) on the right.
    ("J5", SOCK10, "LaunchPad J1", LP["cx"] - LP["row_pitch"] / 2, LPY, 0, "B", "pads",
     {"1": "+3V3", "2": "LED1", "3": "P1.1_RXD", "4": "P1.2_TXD", "5": "P1.3", "6": "VBAT_SENSE",
      "7": "SCK", "8": "OLED_CS", "9": "OLED_DC", "10": "OLED_RST"}),
    ("J6", SOCK10, "LaunchPad J2", LP["cx"] + LP["row_pitch"] / 2, LPY, 0, "B", "pads",
     {"1": "GND", "2": "FLASH_CS", "3": "P2.7", "4": "TEST", "5": "RST", "6": "MOSI",
      "7": "MISO", "8": "SRAM_CS", "9": "AUDIO_PWM", "10": "SR_LOAD"}),
    # ── logic, in the bay under the OLED (front), soldered without sockets ──
    ("U2", "Package_DIP:DIP-16_W7.62mm", "SN74HC165N", 14, 25, 0, "F", "pads",
     {"1": "SR_LOAD", "2": "SCK", "3": "BTN_SELECT", "4": "BTN_START", "5": "BTN_B", "6": "BTN_A",
      "8": "GND", "9": "SR_QH", "10": "GND", "11": "BTN_UP", "12": "BTN_DOWN", "13": "BTN_LEFT",
      "14": "BTN_RIGHT", "15": "GND", "16": "+3V3"}),
    ("U3", DIP8, "23LC1024-I/P", 14, 47, 0, "F", "pads",
     {"1": "SRAM_CS", "2": "MISO", "4": "GND", "5": "MOSI", "6": "SCK", "7": "+3V3", "8": "+3V3"}),
    ("U4", DIP8, "W25Q128 (Adafruit #5634)", 76, 21, 0, "F", "pads",
     {"1": "FLASH_CS", "2": "MISO", "3": "+3V3", "4": "GND", "5": "MOSI", "6": "SCK", "7": "+3V3", "8": "+3V3"}),
    ("U5", DIP8, "LM386N-1", 76, 37.5, 0, "F", "pads",
     {"2": "GND", "3": "AUDIO_IN", "4": "GND", "5": "AMP_OUT", "6": "+5V", "7": "AMP_BYP"}),
    ("C3", C, "100nF", 14, 38.2, 0, "F", "pads", {"1": "+3V3", "2": "GND"}),
    ("C4", C, "100nF", 14, 55.5, 0, "F", "pads", {"1": "+3V3", "2": "GND"}),
    ("C5", C, "100nF", 76, 29.3, 0, "F", "pads", {"1": "+3V3", "2": "GND"}),
    ("C10", C, "100nF", 76, 45.6, 0, "F", "pads", {"1": "+5V", "2": "GND"}),
    # ── power ──
    ("A4", H + "Pololu_S7V8F3", "3.3V buck-boost", 70.3, 48.4, 0, "F", "origin",
     {"1": "PWR_EN", "2": "VBAT", "3": "GND", "4": "+3V3"}),
    ("A2", H + "Adafruit_4410_USBC_MicroLipo", "USB-C LiPo charger", 31.0, 140.0, 90, "B", "origin",
     {"4": "GND", "5": "VBAT"}),
    ("A3", H + "Adafruit_1903_PowerBoost500", "5V boost", 38.0, 76.5, 0, "B", "origin",
     {"1": "VBAT", "2": "GND", "3": "PWR_EN", "5": "GND", "6": "+5V"}),
    ("J1", "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal", "LiPo (JST-PH)", 68.5, 77.5, 180, "F", "pads",
     {"1": "VBAT", "2": "GND"}),
    ("SW9", H + "SW_E-Switch_EG1218", "EG1218 power", *PWR_SWITCH, 0, "B", "origin",
     {"1": "GND", "2": "PWR_EN"}),
    ("R18", R, "470k", 59, 135, 0, "F", "pads", {"1": "VBAT", "2": "VBAT_SENSE"}),
    ("R19", R, "470k", 70, 135, 0, "F", "pads", {"1": "VBAT_SENSE", "2": "GND"}),
    ("C14", C, "100nF", 79, 135, 0, "F", "pads", {"1": "VBAT_SENSE", "2": "GND"}),
    ("C13", CP6, "220uF (OLED kit)", 22, 73, 0, "F", "pads", {"1": "+3V3", "2": "GND"}),
    # ── buttons + pull-ups ──
    *[_btn(i + 1, n) for i, n in enumerate(["UP", "DOWN", "LEFT", "RIGHT", "SELECT", "START", "B", "A"])],
    _pullup("R1", "BTN_UP", 21, 84.5),
    _pullup("R2", "BTN_DOWN", 21, 117.5),
    _pullup("R3", "BTN_LEFT", 9, 91, 90),
    _pullup("R4", "BTN_RIGHT", 33, 90.5, 90),
    _pullup("R5", "BTN_SELECT", 37, 121),
    _pullup("R6", "BTN_START", 53, 121),
    _pullup("R7", "BTN_B", 63, 112),
    _pullup("R8", "BTN_A", 77, 88.5),
    # chip selects idle high while the MCU pins are still inputs after reset
    _pullup("R9", "OLED_CS", 37, 135),
    _pullup("R10", "SRAM_CS", 48, 135),
    _pullup("R11", "FLASH_CS", 63, 116.5),
    # 74HC165 QH is push-pull, never tri-states: isolate it from the shared MISO
    ("R13", R, "1k", 14, 62.5, 0, "F", "pads", {"1": "SR_QH", "2": "MISO"}),
    # ── status LED (LaunchPad LED1 / P1.0) ──
    ("D1", "LED_THT:LED_D3.0mm", "red 3mm", *LED, 0, "F", "pads", {"1": "GND", "2": "LED1_A"}),
    ("R17", R, "1k", 13.5, 68.4, 0, "F", "pads", {"1": "LED1", "2": "LED1_A"}),
    # ── audio ──
    ("R14", R, "1k", 60, 80.5, 0, "F", "pads", {"1": "AUDIO_PWM", "2": "AUDIO_F"}),
    ("C6", C, "100nF", 60, 84.5, 0, "F", "pads", {"1": "AUDIO_F", "2": "GND"}),
    ("C7", CP5, "10uF", 56, 90, 0, "F", "pads", {"1": "AUDIO_F", "2": "VOL_HI"}),
    ("RV1", "Potentiometer_THT:Potentiometer_Bourns_PTV09A-1_Single_Vertical", "10k log (PTV09A)",
     *VOLUME, 0, "F", (7.0, -2.5), {"1": "GND", "2": "AUDIO_IN", "3": "VOL_HI"}),
    ("C8", CP5, "10uF", 81, 104, 90, "F", "pads", {"1": "AMP_BYP", "2": "GND"}),
    ("C11", CP5, "10uF", 81, 112, 90, "F", "pads", {"1": "+5V", "2": "GND"}),
    ("C9", CP6, "220uF", 45, 100, 90, "F", "pads", {"1": "AMP_OUT", "2": "SPK_C"}),
    ("R15", R, "10R", 45, 109, 0, "F", "pads", {"1": "SPK_C", "2": "SPK+"}),
    ("C12", C, "47nF (opt)", 45, 113.5, 0, "F", "pads", {"1": "AMP_OUT", "2": "ZOBEL"}),
    ("R16", R, "10R (opt)", 45, 117, 0, "F", "pads", {"1": "ZOBEL", "2": "GND"}),
    ("J2", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", "Speaker (solder wires)",
     74, 82, 90, "B", "pads", {"1": "SPK+", "2": "GND"}),
]

POWER_NETS = ["GND", "+3V3", "+5V", "VBAT", "AMP_OUT", "SPK_C", "SPK+"]

# Heights above the board surface, for the enclosure fit model (mm).
HEIGHTS = {"U": 4.6, "C_disc": 4.5, "CP": 12.0, "R": 2.6, "SW": 4.3, "RV": 6.5, "D": 17.0,
           "A2": 9.8, "A3": 9.6, "A4": 5.6, "J1": 6.0, "SW9": 7.4, "J5": 8.5, "J6": 8.5, "J2": 2.0}

SILK_F = [  # (text, x, y, size)
    ("MSP430 HANDHELD  rev " + REV, 45, 138.2, 1.2),
    ("BATTERY BAY - no leads here", 45, 42, 1.5),
    ("+", 72.6, 77.5, 1.2), ("LiPo", 67.5, 68.6, 1.0),
    ("VOL", 45, 93.5, 1.0),
]
SILK_B = [
    ("LAUNCHPAD MSP-EXP430G2ET", 45, 20, 1.5),
    ("component side down, USB up", 45, 23.5, 1.0),
    ("J1: VCC..P2.2", 32, LP["pin1_y"] - 3, 0.9), ("J2: GND..P2.3", 58, LP["pin1_y"] - 3, 0.9),
    ("OFF  ON", 71, 127.2, 1.0),
    ("SPK+  GND", 74, 85.3, 1.0),
    ("Generated by pcb/gen_pcb.py - do not hand-edit", 45, 72, 0.9),
]

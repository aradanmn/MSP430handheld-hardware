#!/usr/bin/env python3
"""
gen_pcb.py -- build the handheld carrier PCB from handheld_design.py.

Runs inside KiCad 9's Python (see build.sh; needs the `pcbnew` module).

  gen_pcb.py place  OUT.kicad_pcb     footprints, nets, outline -> unrouted board
  gen_pcb.py dsn    IN.kicad_pcb  OUT.dsn      Specctra export for the autorouter
  gen_pcb.py finish IN.kicad_pcb  IN.ses  OUT.kicad_pcb   import routes, pour GND, save

`place` also writes lib/handheld.pretty/, build/placement.json and
../enclosure/board_params.scad, so the enclosure is always cut from the same
numbers as the copper.
"""
import json, math, os, sys
import pcbnew
import handheld_design as D

HERE = os.path.dirname(os.path.abspath(__file__))
LIBDIR = os.path.join(HERE, "lib", "handheld.pretty")
MM, TO = pcbnew.FromMM, pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(MM(x), MM(y))


# ── custom footprints ────────────────────────────────────────────────────────
def module_footprint_text(name, m):
    ox, oy = m.get("origin", (0, 0))
    s = [f'(footprint "{name}" (version 20240108) (generator "gen_pcb") (layer "F.Cu")',
         f'  (property "Reference" "REF**" (at {m["w"]/2-ox:.3f} {m["h"]-oy+1.2:.3f} 0) (layer "F.SilkS")'
         ' (effects (font (size 0.9 0.9) (thickness 0.14))))',
         f'  (property "Value" "{name}" (at {m["w"]/2-ox:.3f} {m["h"]/2-oy:.3f} 0) (layer "F.Fab")'
         ' (effects (font (size 0.9 0.9) (thickness 0.14))))',
         '  (attr through_hole)']
    def rect(x, y, w, h, layer, width):
        s.append(f'  (fp_rect (start {x-ox:.3f} {y-oy:.3f}) (end {x+w-ox:.3f} {y+h-oy:.3f})'
                 f' (stroke (width {width}) (type solid)) (fill none) (layer "{layer}"))')
    rect(0, 0, m["w"], m["h"], "F.SilkS", 0.15)
    rect(0, 0, m["w"], m["h"], "F.Fab", 0.1)
    if m.get("courtyard", True):
        rect(-0.25, -0.25, m["w"] + 0.5, m["h"] + 0.5, "F.CrtYd", 0.05)
    for x, y, w, h in m["fab"]:
        rect(x, y, w, h, "F.Fab", 0.1)
        rect(x, y, w, h, "F.SilkS", 0.12)
    if m["label"]:
        s.append(f'  (fp_text user "{m["label"]}" (at {m["w"]/2-ox:.3f} {m["h"]*0.62-oy:.3f} 0) (layer "F.SilkS")'
                 ' (effects (font (size 0.9 0.9) (thickness 0.14))))')
    for num, pname, x, y in m["pads"]:
        shape = "rect" if num == "1" else "circle"
        s.append(f'  (pad "{num}" thru_hole {shape} (at {x-ox:.3f} {y-oy:.3f}) (size {m["pad"]} {m["pad"]})'
                 f' (drill {m["drill"]}) (layers "*.Cu" "*.Mask"))')
        if m["silk_names"] and pname:
            s.append(f'  (fp_text user "{pname}" (at {x-ox:.3f} {y-oy+3.4:.3f} 90) (layer "F.SilkS")'
                     ' (effects (font (size 0.7 0.7) (thickness 0.11))))')
    for x, y, d in m["npth"]:
        s.append(f'  (pad "" np_thru_hole circle (at {x-ox:.3f} {y-oy:.3f}) (size {d} {d}) (drill {d})'
                 ' (layers "*.Cu" "*.Mask"))')
    s.append(")")
    return "\n".join(s) + "\n"


def write_library():
    os.makedirs(LIBDIR, exist_ok=True)
    for name, m in D.MODULES.items():
        with open(os.path.join(LIBDIR, name + ".kicad_mod"), "w") as f:
            f.write(module_footprint_text(name, m))


def load_fp(spec):
    lib, name = spec.split(":")
    path = LIBDIR if lib == "handheld" else D.L + lib + ".pretty"
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise SystemExit(f"footprint not found: {spec}")
    fp.SetFPID(pcbnew.LIB_ID(lib, name))      # keep the library link so KiCad can update from the library
    return fp


# ── placement ────────────────────────────────────────────────────────────────
def xform(p, rot, back):
    """Footprint-local point -> offset from the footprint origin after KiCad's
    rotate (CCW positive, y down) and, for the back, left-right flip."""
    a = math.radians(rot)
    x = p[0] * math.cos(a) + p[1] * math.sin(a)
    y = -p[0] * math.sin(a) + p[1] * math.cos(a)
    return (-x if back else x, y)


def pads_centre(fp):
    xs = [TO(p.GetPosition().x) for p in fp.Pads() if p.GetNumber() not in ("", "MP")]
    ys = [TO(p.GetPosition().y) for p in fp.Pads() if p.GetNumber() not in ("", "MP")]
    return ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)


def place(board, nets, part):
    ref, spec, value, x, y, rot, side, anchor, padnets = part
    fp = load_fp(spec)
    fp.SetReference(ref)
    fp.SetValue(value)
    local = {p.GetNumber(): (TO(p.GetPosition().x), TO(p.GetPosition().y)) for p in fp.Pads()}
    a_local = pads_centre(fp) if anchor == "pads" else (0, 0) if anchor == "origin" else anchor
    board.Add(fp)
    fp.SetPosition(V(0, 0))
    fp.SetOrientationDegrees(rot)
    back = side == "B"
    if back:
        fp.Flip(V(0, 0), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    ax, ay = xform(a_local, rot, back)
    fp.SetPosition(V(x - ax, y - ay))
    # The enclosure trusts xform(); prove it matches what KiCad actually did.
    for p in fp.Pads():
        if p.GetNumber() in local and len([q for q in fp.Pads() if q.GetNumber() == p.GetNumber()]) == 1:
            ex, ey = xform(local[p.GetNumber()], rot, back)
            gx, gy = TO(p.GetPosition().x), TO(p.GetPosition().y)
            assert abs(gx - (x - ax + ex)) < 0.01 and abs(gy - (y - ay + ey)) < 0.01, (ref, p.GetNumber())
    used = set()
    for p in fp.Pads():
        n = padnets.get(p.GetNumber())
        if n:
            p.SetNet(nets[n])
            used.add(p.GetNumber())
    missing = set(padnets) - used
    assert not missing, f"{ref}: pads {missing} not in footprint {spec}"
    return fp


def add_text(board, text, x, y, size, layer):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetPosition(V(x, y))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size)))
    t.SetTextThickness(MM(max(0.12, size * 0.15)))
    if layer == pcbnew.B_SilkS:
        t.SetMirrored(True)
    board.Add(t)


def add_rect(board, x, y, w, h, layer, width=0.15):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_RECT)
    s.SetStart(V(x, y)); s.SetEnd(V(x + w, y + h))
    s.SetLayer(layer); s.SetWidth(MM(width))
    board.Add(s)


def add_outline(board):
    W, H, r = D.BOARD_W, D.BOARD_H, D.BOARD_R
    def seg(a, b):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(*a)); s.SetEnd(V(*b)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1)); board.Add(s)
    def arc(c, start, mid, end):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_ARC)
        s.SetArcGeometry(V(*start), V(*mid), V(*end)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1)); board.Add(s)
    k = r * (1 - math.sqrt(0.5))
    seg((r, 0), (W - r, 0)); seg((W, r), (W, H - r)); seg((W - r, H), (r, H)); seg((0, H - r), (0, r))
    arc(None, (W - r, 0), (W - k, k), (W, r))
    arc(None, (W, H - r), (W - k, H - k), (W - r, H))
    arc(None, (r, H), (k, H - k), (0, H - r))
    arc(None, (0, r), (k, k), (r, 0))


def net_settings(board):
    bds = board.GetDesignSettings()
    bds.SetCopperLayerCount(2)
    bds.m_TrackMinWidth = MM(0.2)
    bds.m_MinClearance = MM(0.2)
    bds.m_CopperEdgeClearance = MM(0.5)
    ns = bds.m_NetSettings
    d = ns.GetDefaultNetclass()
    d.SetClearance(MM(0.25)); d.SetTrackWidth(MM(0.3)); d.SetViaDiameter(MM(0.8)); d.SetViaDrill(MM(0.4))
    p = pcbnew.NETCLASS("Power")
    p.SetClearance(MM(0.25)); p.SetTrackWidth(MM(0.6)); p.SetViaDiameter(MM(1.0)); p.SetViaDrill(MM(0.5))
    ns.SetNetclass("Power", p)
    for n in D.POWER_NETS:
        ns.SetNetclassPatternAssignment(n, "Power")


def cmd_place(out):
    write_library()
    board = pcbnew.NewBoard(out)
    net_settings(board)
    names = sorted({n for part in D.PARTS for n in part[8].values()})
    nets = {}
    for n in names:
        ni = pcbnew.NETINFO_ITEM(board, n)
        board.Add(ni)
        nets[n] = ni
    add_outline(board)
    placed = {}
    for part in D.PARTS:
        placed[part[0]] = place(board, nets, part)
    for i, (x, y) in enumerate(D.CASE_SCREWS):
        fp = load_fp("MountingHole:MountingHole_3.2mm_M3")
        fp.SetReference(f"H{i+1}"); fp.SetPosition(V(x, y))
        fp.Reference().SetVisible(False)
        board.Add(fp)
    b = D.BATTERY
    add_rect(board, b["x"], b["y"], b["w"], b["h"], pcbnew.F_SilkS, 0.2)
    s = D.SPEAKER
    c = pcbnew.PCB_SHAPE(board); c.SetShape(pcbnew.SHAPE_T_CIRCLE)
    c.SetCenter(V(s["x"], s["y"])); c.SetEnd(V(s["x"] + s["d"] / 2, s["y"]))
    c.SetLayer(pcbnew.B_SilkS); c.SetWidth(MM(0.2)); board.Add(c)
    for t, x, y, sz in D.SILK_F:
        add_text(board, t, x, y, sz, pcbnew.F_SilkS)
    for t, x, y, sz in D.SILK_B:
        add_text(board, t, x, y, sz, pcbnew.B_SilkS)
    for name, (x, y, _) in D.BUTTONS.items():
        add_text(board, name, x, y + 5.2, 0.9, pcbnew.F_SilkS)

    # one net per pin name on a pad is a schematic-level check: every net needs >= 2 pads
    count = {}
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname():
                count[p.GetNetname()] = count.get(p.GetNetname(), 0) + 1
    single = sorted(n for n, c in count.items() if c < 2)
    assert not single, f"nets with only one pad: {single}"

    pcbnew.SaveBoard(out, board)
    export_placement(board, placed)
    print("placed", len(placed), "parts,", len(names), "nets ->", out)


def export_placement(board, placed):
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    info = {}
    for ref, fp in placed.items():
        back = fp.GetLayer() == pcbnew.B_Cu
        bb = fp.GetCourtyard(pcbnew.B_CrtYd if back else pcbnew.F_CrtYd).BBox()
        info[ref] = dict(side="B" if back else "F", value=fp.GetValue(),
                         box=[round(TO(v), 2) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())],
                         pads={f"{p.GetNumber()}": [round(TO(p.GetPosition().x), 3), round(TO(p.GetPosition().y), 3),
                                                    p.GetNetname()] for p in fp.Pads() if p.GetNumber()})
    json.dump(info, open(os.path.join(HERE, "build", "placement.json"), "w"), indent=1)
    write_scad_params(info)
    write_netlist(info)


def height_of(ref):
    for k in (ref, ref.rstrip("0123456789")):
        if k in D.HEIGHTS:
            return D.HEIGHTS[k]
    if ref.startswith("C"):
        return D.HEIGHTS["CP"] if ref in ("C7", "C8", "C9", "C11", "C13") else D.HEIGHTS["C_disc"]
    return 3.0


def write_scad_params(info):
    o = D.OLED
    usb_c_x = info["A2"]["box"][0] + (info["A2"]["box"][2] - info["A2"]["box"][0]) / 2
    L = ["// GENERATED by pcb/gen_pcb.py from pcb/handheld_design.py -- do not edit.",
         "// Board FRONT-view coordinates: origin top-left of the PCB, x right, y down, mm.",
         f"pcb_w = {D.BOARD_W}; pcb_h = {D.BOARD_H}; pcb_r = {D.BOARD_R}; pcb_t = 1.6;",
         f"case_screws = {json.dumps([list(p) for p in D.CASE_SCREWS])};",
         f"oled_at = {list(o['at'])}; oled_size = [{o['w']}, {o['h']}]; oled_gap = {o['gap']};",
         f"oled_pcb_t = {o['pcb_t']}; oled_bezel = {list(o['bezel'])}; oled_bezel_h = {o['bezel_h']};",
         f"oled_holes = {json.dumps([list(p) for p in o['holes']])};",
         "buttons = [" + ", ".join(f'["{n}", {x}, {y}, "{s}"]' for n, (x, y, s) in D.BUTTONS.items()) + "];",
         f"volume_at = {list(D.VOLUME)}; led_at = {list(D.LED)}; pwr_switch_at = {list(D.PWR_SWITCH)};",
         f"battery = [{D.BATTERY['x']}, {D.BATTERY['y']}, {D.BATTERY['w']}, {D.BATTERY['h']}, {D.BATTERY['t']}];",
         f"speaker = [{D.SPEAKER['x']}, {D.SPEAKER['y']}, {D.SPEAKER['d']}, {D.SPEAKER['t']}];",
         f"usb_c_x = {usb_c_x:.3f};   // charger USB-C centre, bottom edge",
         f"prog_at = [{D.PROG['x']}, {D.PROG['y']}]; prog_n = {D.PROG['n']};   // J3, pins leave through the top wall",
         "// [ref, side, x0, y0, x1, y1, height] courtyard boxes for the fit model",
         "parts = ["]
    for ref, i in info.items():
        if ref == "A1":
            continue
        b = i["box"]
        L.append(f'  ["{ref}", "{i["side"]}", {b[0]}, {b[1]}, {b[2]}, {b[3]}, {height_of(ref)}],')
    L.append("];")
    path = os.path.join(HERE, "..", "enclosure", "board_params.scad")
    open(path, "w").write("\n".join(L) + "\n")


def write_netlist(info):
    nets = {}
    for ref, i in info.items():
        for num, (_, _, net) in i["pads"].items():
            if net:
                nets.setdefault(net, []).append(f"{ref}.{num}")
    L = ["# Netlist (generated by pcb/gen_pcb.py -- do not edit)", "",
         "| Net | Pins |", "|-----|------|"]
    for n in sorted(nets):
        L.append(f"| `{n}` | {', '.join(sorted(set(nets[n]), key=lambda s: (s.split('.')[0], s)))} |")
    L += ["", "| Ref | Value | Side |", "|-----|-------|------|"]
    for ref, i in sorted(info.items(), key=lambda kv: (kv[0].rstrip('0123456789'), int('0' + ''.join(c for c in kv[0] if c.isdigit())))):
        L.append(f"| {ref} | {i['value']} | {'front' if i['side'] == 'F' else 'back'} |")
    open(os.path.join(HERE, "NETLIST.md"), "w").write("\n".join(L) + "\n")


def cmd_dsn(inp, out):
    board = pcbnew.LoadBoard(inp)
    net_settings(board)
    ok = pcbnew.ExportSpecctraDSN(board, out)
    print("DSN export:", ok, out)
    if not ok:
        raise SystemExit(1)


def cmd_finish(inp, ses, out):
    board = pcbnew.LoadBoard(inp)
    net_settings(board)
    if not pcbnew.ImportSpecctraSES(board, ses):
        raise SystemExit("SES import failed")
    # Freerouting occasionally necks a segment down below our 0.2 mm minimum;
    # widen it back and let DRC judge the clearance.
    thin = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T and t.GetWidth() < MM(0.2)]
    for t in thin:
        t.SetWidth(MM(0.2))
    print("widened", len(thin), "under-width segments")
    gnd = board.FindNet("GND")
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer); z.SetNet(gnd); z.SetZoneName("GND")
        z.SetLocalClearance(MM(0.3)); z.SetMinThickness(MM(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(MM(0.3)); z.SetThermalReliefSpokeWidth(MM(0.5))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        ol = z.Outline(); ol.NewOutline()
        for x, y in ((0, 0), (D.BOARD_W, 0), (D.BOARD_W, D.BOARD_H), (0, D.BOARD_H)):
            ol.Append(MM(x), MM(y))
        board.Add(z)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(out, board)
    print("tracks+vias:", len(board.GetTracks()), "->", out)


if __name__ == "__main__":
    {"place": cmd_place, "dsn": cmd_dsn, "finish": cmd_finish}[sys.argv[1]](*sys.argv[2:])

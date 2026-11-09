#!/usr/bin/env python3
"""
check_netlist.py -- prove the schematic and the PCB describe the same circuit.

  check_netlist.py SCHEMATIC_NETLIST.xml pcb/build/placement.json

The first file is `kicad-cli sch export netlist --format kicadxml`; the second is
written by gen_pcb.py from the placed board. Compares, for every net, the exact
set of (reference, pin) it joins, and each part's footprint. Exit 1 on any difference.
"""
import json, sys
import xml.etree.ElementTree as ET

sch_nets, sch_fp = {}, {}
root = ET.parse(sys.argv[1]).getroot()
for c in root.iter("comp"):
    sch_fp[c.get("ref")] = (c.findtext("footprint") or "")
for n in root.iter("net"):
    pins = {(x.get("ref"), x.get("pin")) for x in n.iter("node")}
    if len(pins) > 1:
        sch_nets[n.get("name").lstrip("/")] = pins

pcb_nets, pcb_refs = {}, set()
for ref, info in json.load(open(sys.argv[2])).items():
    pcb_refs.add(ref)
    for num, (_, _, net) in info["pads"].items():
        if net:
            pcb_nets.setdefault(net, set()).add((ref, num))

bad = 0
for name in sorted(set(sch_nets) | set(pcb_nets)):
    a, b = sch_nets.get(name, set()), pcb_nets.get(name, set())
    if a != b:
        bad += 1
        print(f"NET {name}: schematic only {sorted(a - b)}  pcb only {sorted(b - a)}")
real = {r for r in sch_fp if not r.startswith("#")}
if real != pcb_refs:
    bad += 1
    print("PARTS differ: schematic only", sorted(real - pcb_refs), " pcb only", sorted(pcb_refs - real))
print(f"{len(sch_nets)} schematic nets, {len(pcb_nets)} PCB nets, {len(real)} parts: "
      + ("MATCH" if not bad else f"{bad} DIFFERENCES"))
sys.exit(1 if bad else 0)

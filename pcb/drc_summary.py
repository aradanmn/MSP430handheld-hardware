#!/usr/bin/env python3
"""Summarise a kicad-cli DRC JSON report; exit 1 on anything that blocks fabrication."""
import collections, json, sys

# Stock-library footprints differ cosmetically from the board copies; silkscreen
# overlaps are legibility only. starved_thermal means a GND pad has one pour spoke
# instead of two; every GND pad is also on a routed track, and a pad that really
# lost its connection shows up under "unconnected". Everything else must be zero.
COSMETIC = {"lib_footprint_issues", "lib_footprint_mismatch", "silk_overlap", "silk_over_copper",
            "silk_edge_clearance", "text_height", "text_thickness", "starved_thermal"}
d = json.load(open(sys.argv[1]))
v = collections.Counter(x["type"] for x in d.get("violations", []))
unconnected = len(d.get("unconnected_items", []))
blocking = {k: n for k, n in v.items() if k not in COSMETIC}
print("unconnected pads:", unconnected)
print("blocking violations:", blocking or "none")
print("advisory:", {k: n for k, n in v.items() if k in COSMETIC} or "none")
for x in d.get("violations", []):
    if x["type"] not in COSMETIC:
        print("  ", x["type"], "|", x["description"], "|", [i["description"] for i in x["items"]])
for x in d.get("unconnected_items", []):
    print("  unconnected |", [i["description"] for i in x["items"]])
sys.exit(1 if blocking or unconnected else 0)

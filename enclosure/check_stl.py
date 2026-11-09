#!/usr/bin/env python3
"""Check ASCII STLs are closed (every edge shared by exactly two facets) and print bounding boxes.
Usage: check_stl.py FILE.stl [...]   exit 1 if any mesh is open."""
import collections, re, sys

bad = 0
for path in sys.argv[1:]:
    pts = [tuple(round(float(v), 4) for v in m) for m in
           re.findall(r"vertex\s+(\S+)\s+(\S+)\s+(\S+)", open(path).read())]
    edges = collections.Counter()
    for i in range(0, len(pts), 3):
        a, b, c = pts[i:i + 3]
        for e in ((a, b), (b, c), (c, a)):
            edges[e] += 1
    open_edges = sum(1 for (a, b), n in edges.items() if edges.get((b, a), 0) != n)
    lo = [min(p[k] for p in pts) for k in range(3)]
    hi = [max(p[k] for p in pts) for k in range(3)]
    size = " x ".join(f"{h - l:.1f}" for l, h in zip(lo, hi))
    print(f"{path.split('/')[-1]:26s} {len(pts)//3:6d} facets  {size} mm  z0={lo[2]:.2f}  "
          + ("closed" if not open_edges and pts else f"OPEN ({open_edges} unmatched edges)"))
    bad += bool(open_edges) or not pts
sys.exit(1 if bad else 0)

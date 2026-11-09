#!/bin/sh
# Render front/back PNG previews of a board: pcb/view.sh BOARD.kicad_pcb OUTDIR
# (the back view is as seen from behind, i.e. mirrored left-right vs. board coordinates)
set -eu
B="$1"; O="$2"; HERE="$(cd "$(dirname "$0")" && pwd)"   # both paths relative to the repo root
mkdir -p "$HERE/../$O"
for side in top bottom; do
  "$HERE/kicad.sh" kicad-cli pcb render --side $side --width 1000 --height 1500 --zoom 0.9 --quality basic \
    -o "$O/$side.png" "$B" >/dev/null
done

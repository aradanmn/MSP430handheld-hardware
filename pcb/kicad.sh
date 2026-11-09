#!/bin/sh
# Run a command inside the KiCad 9 container with the repo mounted at /work.
# Usage: pcb/kicad.sh python3 pcb/gen_pcb.py place pcb/build/placed.kicad_pcb
set -eu
REPO="$(cd "$(dirname "$0")/.." && pwd)"
exec docker run --rm --network none -u "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$REPO":/work -w /work "${KICAD_IMAGE:-kicad/kicad:9.0}" "$@"

#!/bin/sh
# Full PCB build: place -> autoroute -> pour -> DRC -> fabrication outputs.
# Needs docker (KiCad 9 image + a Java 25 image) and a Freerouting jar:
#   FREEROUTING_JAR=/path/to/freerouting-2.x.jar pcb/build.sh
# The autorouter is not deterministic. REUSE_ROUTE=1 skips place+route and rebuilds
# from the files already in pcb/build/ (not committed).
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"; REPO="$(dirname "$HERE")"
[ "${REUSE_ROUTE:-0}" = 1 ] || JAR="${FREEROUTING_JAR:?set FREEROUTING_JAR to a freerouting 2.x jar}"
B=pcb/build; NAME=msp430_handheld
mkdir -p "$HERE/build" "$HERE/fab" "$HERE/renders"

if [ "${REUSE_ROUTE:-0}" != 1 ]; then
echo "== place";  "$HERE/kicad.sh" python3 pcb/gen_pcb.py place $B/placed.kicad_pcb
echo "== dsn";    "$HERE/kicad.sh" python3 pcb/gen_pcb.py dsn $B/placed.kicad_pcb $B/$NAME.dsn
echo "== route (bounded: ${ROUTE_TIMEOUT:=900}s)"
timeout "$ROUTE_TIMEOUT" docker run --rm --network none --cpus 4 -u "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$HERE/build":/b -v "$JAR":/fr.jar:ro "${JAVA_IMAGE:-eclipse-temurin:25-jre}" \
  java -Djava.awt.headless=true -jar /fr.jar -de /b/$NAME.dsn -do /b/$NAME.ses -mp "${ROUTE_PASSES:-40}" \
  --gui.enabled=false --api_server.enabled=false --usage_and_diagnostic_data.disable_analytics=true \
  > "$HERE/build/route.log" 2>&1 || { tail -20 "$HERE/build/route.log"; echo "routing failed"; exit 1; }
fi
echo "== finish"; "$HERE/kicad.sh" python3 pcb/gen_pcb.py finish $B/placed.kicad_pcb $B/$NAME.ses pcb/$NAME.kicad_pcb
echo "== drc"
"$HERE/kicad.sh" kicad-cli pcb drc --format json --severity-all -o $B/drc.json pcb/$NAME.kicad_pcb
python3 "$HERE/drc_summary.py" "$HERE/build/drc.json" > "$HERE/DRC.txt" || { cat "$HERE/DRC.txt"; echo "DRC FAILED"; exit 1; }
cat "$HERE/DRC.txt"
echo "== schematic (same table as the board) + netlist equivalence"
"$HERE/kicad.sh" sh -c "
  python3 scripts/gen_schematic.py schematic/$NAME.kicad_sch &&
  kicad-cli sch export netlist --format kicadxml -o $B/sch_netlist.xml schematic/$NAME.kicad_sch &&
  kicad-cli sch export pdf -o schematic/$NAME.pdf schematic/$NAME.kicad_sch" 2>&1 | grep -v -i cvpcb | grep -v "Footprint Library Table" | grep -v "library table" || true
python3 "$REPO/scripts/check_netlist.py" "$HERE/build/sch_netlist.xml" "$HERE/build/placement.json"
echo "== outputs"
"$HERE/kicad.sh" sh -c "
  kicad-cli pcb export gerbers -o pcb/fab/ -l F.Cu,B.Cu,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts pcb/$NAME.kicad_pcb &&
  kicad-cli pcb export drill -o pcb/fab/ --excellon-separate-th pcb/$NAME.kicad_pcb &&
  kicad-cli pcb export dxf --mode-single -o pcb/fab/$NAME-outline.dxf -l Edge.Cuts --output-units mm pcb/$NAME.kicad_pcb &&
  kicad-cli pcb export step -o pcb/fab/$NAME.step --subst-models --force pcb/$NAME.kicad_pcb" > "$HERE/build/export.log" 2>&1 \
  || { tail -20 "$HERE/build/export.log"; exit 1; }
"$HERE/view.sh" pcb/$NAME.kicad_pcb pcb/renders
echo "done"

#!/bin/sh
# Export every printable part to enclosure/stl/ and preview images to enclosure/renders/.
# Needs docker (openscad/openscad image). Run pcb/build.sh first so board_params.scad is current.
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$HERE/stl" "$HERE/renders"
scad() { docker run --rm --network none -u "$(id -u):$(id -g)" -e HOME=/tmp -v "$HERE":/e -w /e \
         "${OPENSCAD_IMAGE:-openscad/openscad:latest}" "$@"; }
for p in front back cap_dpad cap_ab cap_pill knob slider; do
  echo "== $p"
  scad openscad -q -D "part=\"$p\"" -o "stl/handheld_$p.stl" handheld_enclosure.scad
done
if [ "${PREVIEWS:-1}" = 1 ]; then
  scad sh -c '
    R="xvfb-run -a openscad -q --imgsize=1200,1500 --colorscheme=Tomorrow"
    $R -D "part=\"front\""    --camera=45,-70,0,35,0,20,420  -o renders/front_shell.png handheld_enclosure.scad
    $R -D "part=\"back\""     --camera=45,-70,0,35,0,20,420  -o renders/back_shell.png  handheld_enclosure.scad
    $R -D "part=\"assembly\"" --camera=45,-70,0,0,0,0,460    -o renders/assembly_front.png handheld_enclosure.scad
    $R -D "part=\"assembly\"" --camera=45,-70,0,180,0,0,460  -o renders/assembly_back.png handheld_enclosure.scad
    $R -D "part=\"section\"" -D cut_x=45 --render --camera=45,-70,0,90,0,90,460 -o renders/section_x45.png handheld_enclosure.scad
    $R -D "part=\"section\"" -D cut_x=21 --render --camera=45,-70,0,90,0,90,460 -o renders/section_x21.png handheld_enclosure.scad
  ' || echo "previews skipped (no xvfb/GL in this image)"
fi

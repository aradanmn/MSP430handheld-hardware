// MSP430 handheld -- 3D-printed enclosure (rev A)
//
// All board-derived numbers come from board_params.scad, which pcb/gen_pcb.py
// writes from the same table the copper is generated from. Edit dimensions
// there (pcb/handheld_design.py), not here.
//
// Coordinates: x = board x (front view), y = -board y, z = 0 at the PCB's
// FRONT surface, +z towards the player.
//
// Select what to export with -D 'part="front"' (see build.sh):
//   front | back | cap_dpad | cap_ab | cap_pill | knob | slider | assembly
include <board_params.scad>

part = "assembly";
$fn = 48;

// ── print / fit parameters ──────────────────────────────────────────────────
wall      = 2.4;     // side walls
face_t    = 2.0;     // front face
back_t    = 2.0;     // back plate
gap       = 0.5;     // PCB edge to wall
fit       = 0.3;     // sliding clearance per side for caps, bezel, knob
lip_h     = 2.0;     // back-shell lip that keys into the front shell
lip_t     = 1.1;

// ── stack heights ───────────────────────────────────────────────────────────
front_h   = oled_gap + oled_pcb_t + oled_bezel_h;   // PCB front -> outer face (bezel sits flush)
face_in   = front_h - face_t;
back_d    = lp_gap + 1.6 + 2.0;                     // PCB back -> inside of back plate (LaunchPad stack)
z_pcb_bk  = -pcb_t;
z_back_in = z_pcb_bk - back_d;
z_back_out= z_back_in - back_t;

// ── part-specific numbers (datasheet values, see DESIGN.md) ─────────────────
sw_top       = 4.3;        // B3F-1000 plunger height above the PCB
cap_proud    = 1.5;
collar_len   = 6.0;        // cap guide below the face
cap_d        = [["dpad", 8.0], ["ab", 10.0]];
pill         = [9.0, 4.5];
knob_d       = 14.0; knob_proud = 3.5; pot_shaft_d = 6.0; pot_flat = 4.5; pot_shaft_top = 20.0;
led_d        = 3.2;
boss_d       = 6.5; pilot_d = 2.6;           // M3 x 20 pan-head screws cut their own thread
screw_d      = 3.4; head_d = 6.2; head_h = 3.0;
usbc_cut     = [13.0, 7.5];  usbc_z = z_pcb_bk - (2.54 + 1.6 + 1.6);       // charger on a 2.54 header
lpusb_cut    = [13.0, 8.5];  lpusb_z = z_pcb_bk - lp_gap + 1.5;            // LaunchPad micro-USB
sw_body_h    = 5.4; sw_act = 2.0; sw_travel = 2.5;                         // EG1218
spk_ring_h   = 3.0;

function bp(p) = [p[0], -p[1]];                       // board (front view) -> model xy
function capd(style) = [for (c = cap_d) if (c[0] == style) c[1]][0];

module rrect(x0, y0, w, h, r) {                       // board-coordinate rounded rectangle (2D)
  translate([x0 + r, -(y0 + h) + r]) offset(r) square([w - 2 * r, h - 2 * r]);
}
module outline(grow) { offset(delta = grow) rrect(0, 0, pcb_w, pcb_h, pcb_r); }
module at(p) { translate(bp(p)) children(); }

// ── front shell ─────────────────────────────────────────────────────────────
module button_hole(b, extra = 0) {
  at([b[1], b[2]])
    if (b[3] == "pill") hull() for (s = [-1, 1]) translate([s * (pill[0] - pill[1]) / 2, 0]) circle(d = pill[1] + 2 * fit + extra);
    else circle(d = capd(b[3]) + 2 * fit + extra);
}

module front_shell() {
  difference() {
    union() {
      // face
      translate([0, 0, face_in]) linear_extrude(face_t) outline(gap + wall);
      // walls
      linear_extrude(front_h) difference() { outline(gap + wall); outline(gap); }
      // cap guide collars
      for (b = buttons) translate([0, 0, face_in - collar_len]) linear_extrude(collar_len + 0.01) button_hole(b, 2.4);
      // screw bosses, down to the PCB
      for (s = case_screws) at(s) translate([0, 0, 0.2]) cylinder(d = boss_d, h = face_in - 0.2 + 0.01);
      // LED light tube
      at(led_at) translate([0, 0, face_in - 4]) cylinder(d = led_d + 2.4, h = 4.01);
    }
    // display window: the OLED's metal bezel comes up flush through the face
    translate([0, 0, face_in - 1]) linear_extrude(face_t + 2)
      offset(delta = fit + 0.1) rrect(oled_at[0] + oled_bezel[0], oled_at[1] + oled_bezel[1], oled_bezel[2], oled_bezel[3], 0.5);
    // buttons, knob, LED
    for (b = buttons) translate([0, 0, 0]) linear_extrude(front_h + 1) button_hole(b);
    at(volume_at) translate([0, 0, face_in - 1]) cylinder(d = knob_d + 2 * fit, h = face_t + 2);
    at(led_at) translate([0, 0, face_in - 5]) cylinder(d = led_d, h = face_t + 7);
    // screw pilots
    for (s = case_screws) at(s) translate([0, 0, -0.01]) cylinder(d = pilot_d, h = 11);
    // rebate for the back shell's lip
    translate([0, 0, -0.01]) linear_extrude(lip_h + 0.3) difference() { outline(gap + lip_t + 0.15); outline(gap - 0.01); }
  }
}

// ── back shell ──────────────────────────────────────────────────────────────
module back_shell() {
  spk = [speaker[0], speaker[1]];
  difference() {
    union() {
      translate([0, 0, z_back_out]) linear_extrude(back_t) outline(gap + wall);
      translate([0, 0, z_back_out]) linear_extrude(-z_back_out) difference() { outline(gap + wall); outline(gap); }
      // alignment lip
      linear_extrude(lip_h) difference() { outline(gap + lip_t); outline(gap); }
      // PCB standoffs
      for (s = case_screws) at(s) translate([0, 0, z_back_in - 0.01]) cylinder(d = boss_d + 0.5, h = back_d + 0.01);
      // speaker locating ring
      at(spk) translate([0, 0, z_back_in - 0.01]) difference() {
        cylinder(d = speaker[2] + 0.5 + 2.4, h = spk_ring_h);
        translate([0, 0, -1]) cylinder(d = speaker[2] + 0.5, h = spk_ring_h + 2);
      }
      // rails that keep the power slider on its axis
      at(pwr_switch_at) for (s = [-1, 1]) translate([-9, s * 4.6 - 0.6, z_back_in - 0.01]) cube([18, 1.2, 2.2]);
      // pads that stop the LaunchPad backing out of its sockets
      for (x = [lp_cx - 14, lp_cx + 14]) at([x, lp_top + lp_len / 2]) translate([-3, -3, z_back_in - 0.01]) cube([6, 6, back_d - lp_gap - 1.6 - 0.3]);
    }
    // case screws: clearance + counterbore from outside
    for (s = case_screws) at(s) {
      translate([0, 0, z_back_out - 1]) cylinder(d = screw_d, h = back_d + back_t + 2);
      translate([0, 0, z_back_out - 0.01]) cylinder(d = head_d, h = head_h);
    }
    // speaker grille
    at(spk) for (r = [0 : 4.5 : speaker[2] / 2 - 4]) for (a = [0 : (r == 0 ? 360 : 360 / round(2 * PI * r / 4.5)) : 359])
      rotate(a) translate([r, 0, z_back_out - 1]) cylinder(d = 2.2, h = back_t + 2, $fn = 16);
    // USB-C (charger) through the bottom wall
    translate([usb_c_x, -pcb_h, usbc_z]) rotate([90, 0, 0]) translate([0, 0, -2]) linear_extrude(wall + gap + 4)
      offset(2) square([usbc_cut[0] - 4, usbc_cut[1] - 4], center = true);
    // micro-USB (LaunchPad) through the top wall
    translate([lp_cx, 0, lpusb_z]) rotate([-90, 0, 0]) translate([0, 0, -2]) linear_extrude(wall + gap + 4)
      offset(2) square([lpusb_cut[0] - 4, lpusb_cut[1] - 4], center = true);
    // power slider slot
    at(pwr_switch_at) translate([0, 0, z_back_out - 1]) linear_extrude(back_t + 2)
      square([4 + sw_travel + 0.6, 3.0], center = true);
  }
}

// ── small parts (modelled in place; build.sh re-orients them for printing) ───
module cap(style) {
  z0 = sw_top + 0.2; zf = face_in - collar_len - 0.3;          // flange rides just under the collar
  module prof(extra) {
    if (style == "pill") hull() for (s = [-1, 1]) translate([s * (pill[0] - pill[1]) / 2, 0]) circle(d = pill[1] + extra);
    else circle(d = capd(style) + extra);
  }
  translate([0, 0, z0]) cylinder(d = 4.5, h = zf - 1.2 - z0 + 0.01);            // pusher on the plunger
  hull() {                                                                       // flange, chamfered so it prints without support
    translate([0, 0, zf - 1.2]) linear_extrude(0.01) prof(0);
    translate([0, 0, zf - 0.6]) linear_extrude(0.6) prof(2.4);
  }
  translate([0, 0, zf - 1.2]) linear_extrude(front_h + cap_proud - (zf - 1.2) - 0.6) prof(0);
  translate([0, 0, front_h + cap_proud - 0.6]) hull() { linear_extrude(0.01) prof(0); translate([0, 0, 0.59]) linear_extrude(0.01) prof(-1.2); }
}

module knob() {
  z0 = 8.0; z1 = front_h + knob_proud;
  difference() {
    union() {
      translate([0, 0, z0]) cylinder(d = knob_d, h = z1 - z0 - 0.8);
      translate([0, 0, z1 - 0.8]) cylinder(d1 = knob_d, d2 = knob_d - 1.6, h = 0.8);
    }
    translate([0, 0, z0 - 0.01]) intersection() {                               // D-bore
      cylinder(d = pot_shaft_d + 0.25, h = pot_shaft_top - z0 + 0.4);
      translate([-(pot_shaft_d + 0.25) / 2, -pot_shaft_d / 2, 0]) cube([pot_flat + 0.2, pot_shaft_d, 20]);
    }
    for (a = [0 : 30 : 359]) rotate(a) translate([knob_d / 2, 0, front_h + 0.3]) cylinder(d = 1.4, h = 10, $fn = 12);  // grip
  }
}

module slider() {                                   // drawn at the switch's centre position
  zs = z_pcb_bk - sw_body_h - 0.3;                  // just clear of the switch body
  zp = z_back_in + 0.25;                            // plate rides on the inside of the back
  difference() {
    union() {
      translate([-8, -3.8, zp]) cube([16, 7.6, 1.5]);                                   // plate
      translate([-2.5, -2.5, zp]) cube([5, 5, zs - zp]);                                // post to the actuator
      translate([-2, -1.3, z_back_out - 1.2]) cube([4, 2.6, zp - (z_back_out - 1.2)]);  // thumb nub
    }
    translate([-(sw_act + 0.3) / 2, -(sw_act + 0.3) / 2, zs - sw_act - 0.4]) cube([sw_act + 0.3, sw_act + 0.3, sw_act + 0.5]);
  }
}

// ── fit model ───────────────────────────────────────────────────────────────
module board_model() {
  color("darkgreen") translate([0, 0, -pcb_t]) linear_extrude(pcb_t) outline(0);
  for (p = parts) color(p[1] == "F" ? "silver" : "dimgray")
    translate([p[2], -p[5], p[1] == "F" ? 0 : -pcb_t - p[6]]) cube([p[4] - p[2], p[5] - p[3], p[6]]);
  color("navy") translate([oled_at[0], -oled_at[1] - oled_size[1], oled_gap]) cube([oled_size[0], oled_size[1], oled_pcb_t]);
  color("black") translate([oled_at[0] + oled_bezel[0], -oled_at[1] - oled_bezel[1] - oled_bezel[3], oled_gap + oled_pcb_t]) cube([oled_bezel[2], oled_bezel[3], oled_bezel_h]);
  color("orange") translate([battery[0], -battery[1] - battery[3], 0.5]) cube([battery[2], battery[3], battery[4]]);
  color("red") translate([lp_cx - lp_w / 2, -lp_top - lp_len, -pcb_t - lp_gap - 1.6]) cube([lp_w, lp_len, 1.6]);
  color("gray") at([speaker[0], speaker[1]]) translate([0, 0, z_back_in]) cylinder(d = speaker[2], h = speaker[3]);
}

module small_parts() {
  for (b = buttons) at([b[1], b[2]]) color("gold") cap(b[3]);
  at(volume_at) color("gold") knob();
  at(pwr_switch_at) color("gold") slider();
}

// Print orientations: front shell face-down, caps/knob top-down, back shell and slider plate-down.
if (part == "front")         translate([0, 0, front_h]) rotate([180, 0, 0]) front_shell();
else if (part == "back")     translate([0, 0, -z_back_out]) back_shell();
else if (part == "cap_dpad") translate([0, 0, front_h + cap_proud]) rotate([180, 0, 0]) cap("dpad");
else if (part == "cap_ab")   translate([0, 0, front_h + cap_proud]) rotate([180, 0, 0]) cap("ab");
else if (part == "cap_pill") translate([0, 0, front_h + cap_proud]) rotate([180, 0, 0]) cap("pill");
else if (part == "knob")     translate([0, 0, front_h + knob_proud]) rotate([180, 0, 0]) knob();
else if (part == "slider")   translate([0, 0, -(z_back_out - 1.2)]) slider();
else if (part == "section")  difference() { union() { front_shell(); back_shell(); board_model(); small_parts(); }
                                            translate([cut_x, -500, -100]) cube([500, 1000, 200]); }
else { board_model(); small_parts(); %front_shell(); %back_shell(); }
cut_x = 45;

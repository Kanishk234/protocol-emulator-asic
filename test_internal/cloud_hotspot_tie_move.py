"""One actual congestion-net endpoint relocation; original fixed-buffer source.

Only one tiehi changes placement, by two rows of identical vertical power
phase. No padding, other movement, master, net, clock or margin change.
Reuses authenticated producer and six explicit estimated shell STA cases.
"""
import json
import os
from pathlib import Path

import cloud_cfg_fanout as cfg
import cloud_hotspot_padding as producer

ROOT = cfg.ROOT
TARGET = "u_shell.u_spi._251__684"
OLD_BOX = (89280, 510300, 91200, 514080)
NEW_BOX = (91680, 502740, 93600, 506520)
INPUT = ROOT / "build/hotspot_tie_input"
OUT = ROOT / "build/hotspot_tie_move"

# Keep the original geometry/census setup and conservative orientation
# restoration guard. Replace the complete five-cell selection/padding/moves.
SETUP = producer.EDIT.split("set selected {}", 1)[0]
FINISH = producer.EDIT.split("census ${::env(WARP_AFTER)}.canonical", 1)[1]
MOVE = r'''
set name {u_shell.u_spi._251__684}
set inst [$block findInst $name]
if {$inst eq "NULL" || [[$inst getMaster] getName] ne "sg13cmos5l_tiehi"
    || [$inst getPlacementStatus] ne "PLACED" || [$inst getOrient] ne "MY"} {
    error "Exact tie endpoint source differs"
}
set box [$inst getBBox]
if {$dbu != 1000 || $site != 480 || [$box xMin] != 89280
    || [$box yMin] != 510300 || [$box xMax] != 91200 || [$box yMax] != 514080} {
    error "Exact tie source geometry differs"
}
if {(91680-89280)%$site != 0 || (502740-510300)%(2*3780) != 0} {
    error "Tie target changes site alignment or vertical power phase"
}
set out [open $::env(WARP_SELECTION) w]; puts $out $name; close $out
$inst setLocation 91680 502740
set moved [$inst getBBox]
if {[$moved xMin] != 91680 || [$moved yMin] != 502740
    || [$moved xMax] != 93600 || [$moved yMax] != 506520} {
    error "Native endpoint target geometry differs"
}
census ${::env(WARP_AFTER)}.canonical
'''
EDIT = SETUP + MOVE + FINISH


def audit_move(before, after, geometry_before, geometry_after, selected):
    old, opins = cfg.parse_census(before)
    new, npins = cfg.parse_census(after)
    dbu, site, obox = producer.boxes(geometry_before)
    ndu, nsite, nbox = producer.boxes(geometry_after)
    if (set(old) != set(new) or len(old) != 3606 or opins != npins
            or (dbu, site) != (1000, 480) or (ndu, nsite) != (dbu, site)
            or set(obox) != set(old) or set(nbox) != set(old) or selected != [TARGET]):
        raise ValueError("Source scope, connectivity or geometry units changed")
    endpoints = {key[1]: value for key, value in opins.items()
                 if key[0] == "PIN" and value[-1].replace("\\", "") == "net683"}
    if endpoints != {"u_shell.u_spi._251_/RESET_B": ["INPUT", "SIGNAL", "net683"],
                     TARGET + "/L_HI": ["OUTPUT", "SIGNAL", "net683"]}:
        raise ValueError("Expected two-pin local reset net differs")
    if old[TARGET] != ["sg13cmos5l_tiehi", "91200 510300", "MY", "PLACED"]:
        raise ValueError("Exact original tie placement differs")
    if obox[TARGET] != ("CORE", OLD_BOX) or nbox[TARGET] != ("CORE", NEW_BOX):
        raise ValueError("Endpoint move does not match exact plan")
    moved = []
    for name in old:
        if old[name][0] != new[name][0] or old[name][2:] != new[name][2:]:
            raise ValueError("Master/orientation/status changed: " + name)
        if name != TARGET and (old[name] != new[name] or obox[name] != nbox[name]):
            raise ValueError("Unexpected other instance movement: " + name)
        if old[name] != new[name]:
            moved.append(name)
    if moved != [TARGET] or new[TARGET][1] != "93600 502740":
        raise ValueError("Native MY origin or move census differs")
    return {"changed_instances": moved, "original_box_dbu": OLD_BOX,
            "candidate_box_dbu": NEW_BOX, "dbu_per_um": dbu, "site_width_dbu": site,
            "row_delta": -2, "orientation_status_and_vertical_power_phase_preserved": True,
            "all_other_instances_exact": True, "actual_connectivity_exact": True,
            "local_net683_endpoints": endpoints, "padding_added": False,
            "coarse_route_demand_improvement_unproven": True}


def main():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise ValueError("Native execution is GitHub-only")
    # Isolated process-local adapter; original producer retains every source,
    # policy, native legality and six-corner positive-slack/electrical guard.
    producer.INPUT, producer.OUT = INPUT, OUT
    producer.EDIT, producer.audit_placement = EDIT, audit_move
    try:
        producer.main()
    finally:
        path = OUT / "result.json"
        if path.is_file():
            result = json.loads(path.read_text())
            result["scope"] = "single net683 tie endpoint placement; no padding"
            result["no_fullchip_or_timing_promotion"] = True
            path.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()

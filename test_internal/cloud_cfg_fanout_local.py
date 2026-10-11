"""Cloud-only ten-buffer counterfactual with zero original placement changes.

Reuse the authenticated cluster-eight source, identical buffer insertion and
six explicit-corner STA runs from cloud_cfg_fanout. Change only legalization:
temporarily FIRM all original PLACED cells, restore their exact statuses, and
require identical master/origin/orientation/status for all 3596 originals.
No routing or physical/configured timing acceptance is claimed.

Inherited source: run37811985079 cluster8, no stronger-driver ECO; archive
d32c6375fffb932ce77cce3da5df82dc3477c78e8ba7feed222fa10fb87db112.
Exact ODB/NL/SDC hashes remain guarded by inherited.DERIVED. Same buf_2 masters,
same two six-load groups per column, initial centroids, 20ns clock, original
three corners, Liberty8/SDC10 fanout limits and original macro views remain.
This tests incidental legalization movement, not a claimed congestion remedy:
CRC/SPI/clock routing can remain congested even with unchanged originals.

Pinned OpenROAD provenance:
https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/odb/include/odb/dbTypes.h
dbPlacementStatus FIRM is immovable to the placer; detailed placement reserves
fixed cells and updates only non-fixed standard cells (src/dpl/src/Opendp.cpp).
"""
import argparse
import hashlib
import json
from pathlib import Path

import cloud_cfg_fanout as inherited

INHERITED_SHA = "2f12b4c66f766ef609c25c72a2c7c9fadbe2972538c587c0f5db02f154e18284"
ORIGINAL_INSTANCES = 3596
OUT = inherited.ROOT / "build/cfg_fanout_local"

SNAPSHOT = r"""
check_placement -verbose
set original_instances {}
set original_movable_count 0
foreach original [$block getInsts] {
    set name [$original getName]
    if {[dict exists $original_instances $name]} {error "Duplicate original instance"}
    set status [$original getPlacementStatus]
    dict set original_instances $name [list [[$original getMaster] getName] \
        [$original getOrigin] [$original getOrient] $status]
    if {$status eq "PLACED"} {
        incr original_movable_count
    } elseif {$name ne "u_fabric" || $status ne "FIRM"} {
        error "Unexpected original placement status: $name $status"
    }
}
if {[dict size $original_instances] != 3596 || $original_movable_count != 3595} {
    error "Original instance/status census differs from authenticated cluster-eight source"
}
"""

LEGALIZE = r"""
# Freeze only the authenticated originals. The same ten new cells remain
# movable at exactly the inherited initial centroid positions.
dict for {name expected} $original_instances {
    set original [$block findInst $name]
    if {[lindex $expected 3] eq "PLACED"} {$original setPlacementStatus FIRM}
}
set placement_failed [catch {detailed_placement} placement_error placement_options]
# Always restore source statuses before census, including unsuccessful trials.
dict for {name expected} $original_instances {
    set original [$block findInst $name]
    if {$original eq "NULL"} {error "Original instance disappeared: $name"}
    $original setPlacementStatus [lindex $expected 3]
}
census $::env(WARP_AFTER)
dict for {name expected} $original_instances {
    set original [$block findInst $name]
    set actual [list [[$original getMaster] getName] [$original getOrigin] \
        [$original getOrient] [$original getPlacementStatus]]
    if {$actual ne $expected} {error "Original instance changed despite protection: $name"}
}
puts "WARP_LOCAL_LEGALIZATION original_instances=3596 original_moved=0 original_orientation_changes=0 original_status_changes=0"
if {$placement_failed} {
    # Diagnostic only: never publish this under the successful buffered path.
    write_db ${::env(WARP_OUTPUT_ODB)}.failed_legalization
    return -options $placement_options $placement_error
}
check_placement -verbose
"""


def local_edit():
    source = inherited.EDIT
    start = "census $::env(WARP_BEFORE)\n"
    legalization = "detailed_placement\ncheck_placement -verbose\n"
    if source.count(start) != 1 or source.count(legalization) != 1:
        raise ValueError("Inherited mutation boundaries changed")
    return source.replace(start, start + SNAPSHOT, 1).replace(legalization, LEGALIZE, 1)


def verify_immobility(before, after):
    result = ORIGINAL_VERIFY(before, after)
    old, _ = inherited.parse_census(before)
    new, _ = inherited.parse_census(after)
    if len(old) != ORIGINAL_INSTANCES:
        raise ValueError("Original census is not exactly3596")
    if any(new.get(name) != values for name, values in old.items()):
        raise ValueError("Original master/origin/orientation/status changed")
    if result["original_cells_moved"] or result["original_cell_max_manhattan_displacement_database_units"]:
        raise ValueError("Original placement moved")
    result.update({"original_placement_orientation_status_exact": True,
                   "legalization_policy": "original_PLACED_temporarily_FIRM_then_restore"})
    return result


ORIGINAL_VERIFY = inherited.verify_connections


def run():
    path = Path(inherited.__file__)
    if hashlib.sha256(path.read_bytes()).hexdigest() != INHERITED_SHA:
        raise ValueError("Inherited authenticated implementation changed; review before running")
    inherited.OUT = OUT
    inherited.EDIT = local_edit()
    inherited.verify_connections = verify_immobility
    try:
        inherited.run()
    finally:
        result_path = OUT / "result.json"
        if result_path.exists():
            result = json.loads(result_path.read_text())
            result.update({"counterfactual": "identical_ten_buffers_zero_original_movement",
                           "inherited_helper_sha256": INHERITED_SHA,
                           "inherited_source_archive_sha256": inherited.SOURCE_SHA,
                           "original_instance_count_expected": ORIGINAL_INSTANCES,
                           "grt_next_step": "only after strict legality, topology and six STA guards pass; pair baseline/candidate with identical settings, require actual zero overflow; no detailed route here"})
            # Even an unsuccessful legalizer can leave useful topology and
            # restored-original census evidence. It never changes passed=False.
            before, after = OUT / "before.tsv", OUT / "after.tsv"
            if not result.get("passed") and before.exists() and after.exists():
                try:
                    result["failed_trial_census"] = verify_immobility(before.read_text(), after.read_text())
                except ValueError as exc:
                    result["failed_trial_census_error"] = str(exc)
            result_path.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    run()

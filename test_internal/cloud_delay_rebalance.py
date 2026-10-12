"""D-090: smaller delay cells only where measured fast hold slack >=0.3ns."""
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import cloud_hold_allocation as source
import cloud_cfg_fanout as cfg
import cloud_hotspot_padding as guards

ROOT = source.ROOT
OUT = ROOT / "build/delay_rebalance"
OLD = "sg13cmos5l_dlygate4sd3_1"
NEW = "sg13cmos5l_dlygate4sd2_1"
EVIDENCE_SHA = "3866682f1cbb486f1bbd1f39e642406b89d765dcede5f3b26563217a22c3a0f8"
EDIT = r'''
read_db $::env(WARP_INPUT_ODB)
set block [ord::get_db_block]
set master [[ord::get_db] findMaster sg13cmos5l_dlygate4sd2_1]
if {$master == "NULL"} {error "Missing smaller delay master"}
set file [open $::env(WARP_SELECTED) r]
set names [split [string trim [read $file]] "\n"]
close $file
if {[llength $names] != 251} {error "Wrong measured selected-cell count"}
foreach name $names {
    set inst [$block findInst $name]
    if {$inst == "NULL" || [[$inst getMaster] getName] ne "sg13cmos5l_dlygate4sd3_1"} {error "Wrong selected delay master"}
    if {![$inst swapMaster $master]} {error "Native master swap failed"}
}
check_placement -verbose
census $::env(WARP_AFTER)
set out [open $::env(WARP_GEOMETRY) w]
set widths {}
foreach row [$block getRows] {lappend widths [[$row getSite] getWidth]}
set widths [lsort -unique $widths]
if {[llength $widths] != 1} {error "Nonuniform site"}
puts $out "META\t[$block getDbUnitsPerMicron]\t[lindex $widths 0]"
foreach inst [$block getInsts] {
    set box [$inst getBBox]
    puts $out "BOX\t[$inst getName]\t[[$inst getMaster] getType]\t[$box xMin]\t[$box yMin]\t[$box xMax]\t[$box yMax]"
}
close $out
write_db $::env(WARP_OUTPUT_ODB)
write_verilog $::env(WARP_OUTPUT_NL)
'''


def select(result):
    if result.get("observation_complete") is not True or result.get("source_run") != 38167697696:
        raise ValueError("Incomplete/wrong native source observation")
    queries = result["corners"]["nom_fast_1p32V_m40C"]["queries"]["min"]
    if len(queries) != 590 or any(x["state"] != "CONSTRAINED" for x in queries.values()):
        raise ValueError("Wrong native delay query census")
    selected = {name for name, row in queries.items() if Decimal(row["slack_ns"]) >= Decimal("0.3")}
    if len(selected) != 251: raise ValueError("Measured threshold selection differs")
    return selected


def audit_change(before, after, old_geometry, new_geometry, selected):
    old, old_pins = cfg.parse_census(before); new, new_pins = cfg.parse_census(after)
    if set(old) != set(new) or len(old) != 3606 or old_pins != new_pins:
        raise ValueError("Instances or actual connections changed")
    dbu, site, ob = guards.boxes(old_geometry); ndu, nsite, nb = guards.boxes(new_geometry)
    if (dbu, site, set(ob)) != (ndu, nsite, set(nb)) or set(ob) != set(old):
        raise ValueError("Geometry scope differs")
    if not selected.issubset(old): raise ValueError("Selected delay missing from census")
    saved = 0
    for name, record in old.items():
        if name not in selected:
            if record != new[name] or ob[name] != nb[name]: raise ValueError("Unselected instance changed")
            continue
        if record[0] != OLD or new[name][0] != NEW or record[1:] != new[name][1:]:
            raise ValueError("Unexpected master/location/orientation/status change")
        kind, b = ob[name]; nkind, n = nb[name]
        if kind != "CORE" or nkind != kind or n[1] != b[1] or n[3] != b[3] or n[0] < b[0] or n[2] > b[2]:
            raise ValueError("Delay footprint did not stay inside original bbox")
        if b[2]-b[0] != 4320 or n[2]-n[0] != 3840 or b[3]-b[1] != 3780:
            raise ValueError("Native delay dimensions differ")
        saved += (b[2]-b[0] - n[2]+n[0])*(b[3]-b[1])
    return {"selected_cells": len(selected), "unchanged_connectivity_and_origins": True,
            "unselected_instances_exact": True, "core_bbox_area_saved_um2": saved/(dbu*dbu)}


def main():
    OUT.mkdir(exist_ok=False)
    result = {"producer_passed": False, "physical_acceptance": False, "routing_executed": False,
              "source_run": 38167697696, "timing_source_run": 38315257114, "corners": {}}
    def save(): (OUT / "result.json").write_text(json.dumps(result, indent=2)+"\n")
    save()
    try:
        for name, digest in source.EXPECTED.items():
            if cfg.sha(source.SOURCE/name) != digest: raise ValueError("Original producer changed")
        archive = ROOT / "build/fanout-preflight-source.tar.gz"
        if cfg.sha(archive) != cfg.SOURCE_SHA: raise ValueError("Original archive changed")
        source.prepare_payload(archive, source.SOURCE / "original_source")
        evidence = ROOT / "build/delay_rebalance_input/timing/result.json"
        if cfg.sha(evidence) != EVIDENCE_SHA: raise ValueError("Timing observation differs")
        selected = select(json.loads(evidence.read_text()))
        (OUT / "selected.txt").write_text("\n".join(sorted(selected))+"\n")
        script = OUT / "edit.tcl"; script.write_text(cfg.CENSUS + EDIT)
        env = {"WARP_INPUT_ODB": source.SOURCE/"padded.odb", "WARP_SELECTED": OUT/"selected.txt",
            "WARP_AFTER":OUT/"after.tsv", "WARP_GEOMETRY":OUT/"geometry_after.tsv",
            "WARP_OUTPUT_ODB":OUT/"candidate.odb", "WARP_OUTPUT_NL":OUT/"candidate.nl.v"}
        command=["docker","run","--rm","-v",f"{ROOT}:{ROOT}","-w",str(ROOT)]
        for key, value in env.items(): command.extend(["-e",f"{key}={value}"])
        command.extend(["--entrypoint","openroad",cfg.IMAGE,"-exit",str(script)])
        with (OUT/"edit.log").open("w") as log:
            subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
        result["audit"] = audit_change((source.SOURCE/"after.tsv").read_text(),(OUT/"after.tsv").read_text(),
            (source.SOURCE/"geometry_after.tsv").read_text(),(OUT/"geometry_after.tsv").read_text(),selected)
        config = json.loads((source.SOURCE/"config.json").read_text()); guards.OUT = OUT
        sdc = source.SOURCE/"padded_sta_nom_typ_1p20V_25C/final/sdc/tt_um_warp.sdc"
        if cfg.sha(sdc) != "2fd4e213532d83ee258899b6fc1ed48c4e5d91ddb0ccbe21eea0226cc90fd56e":
            raise ValueError("Source SDC differs")
        for corner in config["STA_CORNERS"]:
            guard=guards.sta(config,"candidate_"+corner,OUT/"candidate.odb",OUT/"candidate.nl.v",sdc,corner)
            if guard["metrics"][f"timing__hold__ws__corner:{corner}"] < 0.1:
                raise ValueError("Original additional 0.1ns hold guard lost")
            result["corners"][corner] = guard; save()
        for name, digest in source.EXPECTED.items():
            if cfg.sha(source.SOURCE/name) != digest: raise ValueError("Original producer modified")
        result["candidate_sha256"] = {name:cfg.sha(OUT/name) for name in ("candidate.odb","candidate.nl.v")}
        result["producer_passed"] = True
    except Exception as exc:
        result["error"] = str(exc); raise
    finally: save()


if __name__ == "__main__": main()

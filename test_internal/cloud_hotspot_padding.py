"""Bounded native local-padding producer and six estimated shell STA checks.

Baseline is exact fixed-original candidate38101405271 (fanout zero). Only
placement padding changes; no routing, RTL, masters or electrical policy edits.
Native geometry proves effective whitespace; policy is not persisted in ODB.
"""
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tarfile

import cloud_cfg_fanout as cfg
from cloud_fanout_local_grt import BUFFERED, CORNERS, validate_candidate
from cloud_fanout_grt import authenticate_views

ROOT = cfg.ROOT
INPUT = ROOT / "build/hotspot_padding_input"
OUT = ROOT / "build/hotspot_padding"

EDIT = r'''
read_db $::env(WARP_INPUT_ODB)
set block [ord::get_db_block]
set dbu [$block getDbUnitsPerMicron]
if {$dbu <= 0} {error "Invalid native units"}
set widths {}
foreach row [$block getRows] {lappend widths [[$row getSite] getWidth]}
set widths [lsort -unique $widths]
if {[llength $widths] != 1 || [lindex $widths 0] <= 0} {error "Nonuniform native site width"}
set site [lindex $widths 0]
proc geometry {path} {
    global block dbu site
    set out [open $path w]
    puts $out "META\t$dbu\t$site"
    foreach inst [$block getInsts] {
        set box [$inst getBBox]
        puts $out "BOX\t[$inst getName]\t[[$inst getMaster] getType]\t[$box xMin]\t[$box yMin]\t[$box xMax]\t[$box yMax]"
    }
    close $out
}
check_placement -verbose
census $::env(WARP_BEFORE)
geometry $::env(WARP_GEOMETRY_BEFORE)
set original_orientation {}
foreach inst [$block getInsts] {
    dict set original_orientation [$inst getName] [list [$inst getOrient] [$inst getPlacementStatus]]
}
set selected {}
foreach inst [$block getInsts] {
    set name [$inst getName]
    if {![string match {u_shell.u_crc.*} $name] && ![string match {u_shell.u_spi.*} $name]} {continue}
    if {[$inst getPlacementStatus] ne "PLACED" || [[$inst getMaster] getType] ne "CORE"} {error "Target is not a movable standard cell"}
    set box [$inst getBBox]
    if {[$box xMin] < 121.44*$dbu && [$box xMax] > 0 && [$box yMin] < 525.6*$dbu && [$box yMax] > 475.2*$dbu} {
        lappend selected $name
    }
}
if {[llength $selected] == 0} {error "No actual target cells"}
set out [open $::env(WARP_SELECTION) w]
foreach name [lsort $selected] {puts $out $name}
close $out
# Native setter forwards each dbInst to Opendp::setPadding(inst,1,1).
foreach name $selected {dpl::set_padding_inst [$block findInst $name] 1 1}
# Positive values are required: zero selects native defaults, not zero movement.
# Pinned Tcl converts22um to45 horizontal sites and5 rows on this source.
detailed_placement -max_displacement {22 22}
census ${::env(WARP_AFTER)}.canonical
geometry ${::env(WARP_GEOMETRY_AFTER)}.canonical
# Undo OpenDP orientation normalization at the SAME legalized physical bbox.
foreach inst [$block getInsts] {
    lassign [dict get $original_orientation [$inst getName]] orient status
    if {[$inst getPlacementStatus] ne $status} {error "Native placement status changed"}
    if {[$inst getOrient] ne $orient} {
        if {$status ne "PLACED"} {error "Native fixed orientation changed"}
        set box [$inst getBBox]
        set left [$box xMin]; set bottom [$box yMin]
        set right [$box xMax]; set top [$box yMax]
        $inst setOrient $orient
        $inst setLocation $left $bottom
        set restored [$inst getBBox]
        if {[$restored xMin] != $left || [$restored yMin] != $bottom || [$restored xMax] != $right || [$restored yMax] != $top} {
            error "Restored orientation changed legalized physical bbox"
        }
    }
}
check_placement -verbose
census $::env(WARP_AFTER)
geometry $::env(WARP_GEOMETRY_AFTER)
write_db $::env(WARP_OUTPUT_ODB)
write_verilog $::env(WARP_OUTPUT_NL)
'''


def boxes(text):
    lines = text.splitlines()
    header = lines.pop(0).split("\t")
    if len(header) != 3 or header[0] != "META": raise ValueError("Missing native geometry units")
    dbu, site = map(int, header[1:])
    if dbu <= 0 or site <= 0: raise ValueError("Invalid native geometry units")
    result = {}
    for line in lines:
        row = line.split("\t")
        if len(row) != 7 or row[0] != "BOX" or row[1] in result: raise ValueError("Malformed/duplicate native box")
        coords = tuple(map(int, row[3:]))
        if coords[2] <= coords[0] or coords[3] <= coords[1]: raise ValueError("Invalid native instance box")
        result[row[1]] = (row[2], coords)
    return dbu, site, result


def gap_witnesses(geometry, selected):
    dbu, site, instances = boxes(geometry)
    witnesses = []
    for name in sorted(selected):
        kind, a = instances[name]
        if kind != "CORE": raise ValueError("Selected geometry is not standard cell")
        for peer, (_, b) in instances.items():
            if name == peer or min(a[3], b[3]) <= max(a[1], b[1]): continue
            gap = b[0]-a[2] if b[0] >= a[2] else a[0]-b[2] if a[0] >= b[2] else -1
            required = site * (2 if peer in selected else 1)
            if gap < required:
                witnesses.append({"selected": name, "peer": peer, "gap_dbu": gap, "required_dbu": required})
    return witnesses


def audit_placement(before, after, geometry_before, geometry_after, selected):
    old, opins = cfg.parse_census(before); new, npins = cfg.parse_census(after)
    if set(old) != set(new) or opins != npins or len(old) != 3606: raise ValueError("Instances or actual connectivity changed")
    dbu, site, obox = boxes(geometry_before); ndu, nsite, nbox = boxes(geometry_after)
    if (dbu, site, set(obox)) != (ndu, nsite, set(nbox)) or set(obox) != set(old): raise ValueError("Native geometry changed scope")
    from decimal import Decimal
    expected = {name for name, (kind, rect) in obox.items() if kind == "CORE" and
        name.startswith(("u_shell.u_crc.", "u_shell.u_spi.")) and
        rect[0] < Decimal('121.44')*dbu and rect[2] > 0 and
        rect[1] < Decimal('525.6')*dbu and rect[3] > Decimal('475.2')*dbu}
    if not selected or set(selected) != expected or len(selected) != len(set(selected)): raise ValueError("Native selected set is not exact measured region")
    moved = []
    for name, value in old.items():
        if value[0] != new[name][0] or value[2:] != new[name][2:]: raise ValueError("Master/orientation/status changed: " + name)
        if obox[name][0] != nbox[name][0]: raise ValueError("Native master type changed")
        oldrect, newrect = obox[name][1], nbox[name][1]
        if (oldrect[2]-oldrect[0],oldrect[3]-oldrect[1]) != (newrect[2]-newrect[0],newrect[3]-newrect[1]): raise ValueError("Actual native cell dimensions changed")
        box_delta = tuple(abs(a-b) for a,b in zip(oldrect,newrect))
        if max(box_delta) > 22*dbu: raise ValueError("Actual native bbox movement exceeds22um bound")
        original = tuple(map(int, value[1].split())); actual = tuple(map(int, new[name][1].split()))
        delta = tuple(abs(a-b) for a,b in zip(original, actual))
        if len(delta) != 2 or max(delta) > 22*dbu: raise ValueError("Movement exceeds22um per-axis bound")
        if any(delta): moved.append({"instance": name, "axis_displacement_dbu": delta,
                                    "bbox_displacement_dbu": box_delta})
        if name == "u_fabric" and (value != new[name] or obox[name] != nbox[name]): raise ValueError("Fixed macro changed")
    pre = gap_witnesses(geometry_before, selected)
    post = gap_witnesses(geometry_after, selected)
    if post: raise ValueError("Effective one-site geometry failed: " + str(post[0]))
    if not pre: raise ValueError("Selected region already has requested padding; no policy-effect witness")
    return {"instances": len(old), "selected_cells": len(selected), "selected_names": selected,
            "native_dbu_per_micrometer": dbu, "native_site_width_dbu": site,
            "preexisting_padding_conflict_witnesses": pre, "post_padding_conflicts": 0,
            "effective_geometry_proved": True, "moved_instances": moved,
            "masters_orientation_status_connectivity_exact": True, "fixed_macro_exact": True}


def sta(config, label, odb, nl, sdc, corner):
    selected = cfg.single_corner_config(config, corner)
    path = OUT / (label + "_config.json"); path.write_text(json.dumps(selected))
    state = OUT / (label + "_state.json"); state.write_text(json.dumps({"odb":str(odb),"nl":str(nl),"sdc":str(sdc),"metrics":{}}))
    run = OUT / label
    run.mkdir(exist_ok=False)
    command = [sys.executable,"-m","librelane","--docker-no-tty","--dockerized","--pdk","ihp-sg13cmos5l",
        "--pdk-root",os.environ["PDK_ROOT"],"--manual-pdk","--hide-progress-bar","--force-run-dir",str(run),
        "--with-initial-state",str(state),str(path)]
    with (OUT / (label + ".log")).open("w") as log:
        subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=300)
    stages=list(run.glob("*-openroad-stamidpnr"))
    if len(stages)!=1: raise ValueError("Missing unique actual STA stage")
    resolved=json.loads((stages[0]/"config.json").read_text())
    if resolved["CELL_LIBS"] != config["LIB"] or cfg.macro_contract(resolved["MACROS"]) != cfg.macro_contract(config["MACROS"]): raise ValueError("STA library/macro changed")
    for key in ("CLOCK_PORT","CLOCK_PERIOD","CLOCK_UNCERTAINTY_CONSTRAINT","CLOCK_TRANSITION_CONSTRAINT","MAX_FANOUT_CONSTRAINT","PNR_SDC_FILE","FALLBACK_SDC","PNR_CORNERS","DEFAULT_CORNER"):
        if resolved.get(key)!=selected.get(key): raise ValueError("STA constraint changed: " + key)
    metrics=json.loads((stages[0]/"state_out.json").read_text())["metrics"]
    cfg.exact_corner_fanout(metrics,corner)
    for stem in ("max_fanout","max_slew","max_cap"):
        if metrics.get(f"design__{stem}_violation__count__corner:{corner}")!=0: raise ValueError("Electrical corner violation: " + stem)
    for kind in ("setup","hold"):
        value=metrics.get(f"timing__{kind}__ws__corner:{corner}")
        if not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0 or metrics.get(f"timing__{kind}_vio__count__corner:{corner}")!=0: raise ValueError("Timing corner failure")
    return {"corner":corner,"metrics":metrics,"odb_sha256":cfg.sha(odb),"nl_sha256":cfg.sha(nl),"sdc_sha256":cfg.sha(sdc)}


def main():
    OUT.mkdir(exist_ok=False)
    result={"passed":False,"source_run":38101405271,"physical_or_timing_acceptance":False,"configured_timing_acceptance":False,"routing_executed":False}
    def save(): (OUT/"result.json").write_text(json.dumps(result,indent=2)+"\n")
    save()
    try:
        source=INPUT/"fixed_original"
        result["source_immobility"]=validate_candidate(source)
        baseline={"odb":source/"buffered.odb","nl":source/"buffered.nl.v","sdc":source/"buffered_sta_nom_typ_1p20V_25C/final/sdc/tt_um_warp.sdc"}
        authenticate_views(baseline,BUFFERED)
        archive=ROOT/"build/fanout-preflight-source.tar.gz"
        if cfg.sha(archive)!=cfg.SOURCE_SHA: raise ValueError("Original source archive differs")
        unpack=OUT/"original_source";unpack.mkdir()
        with tarfile.open(archive) as tf: tf.extractall(unpack,filter="data")
        bundle=unpack/"fanout_source";manifest=json.loads((bundle/"manifest.json").read_text())
        if manifest["source_odb_sdc_nl"]!=cfg.EXPECTED: raise ValueError("Wrong original source manifest")
        for name,digest in manifest["files"].items():
            path=(bundle/name).resolve()
            if not path.is_relative_to(bundle.resolve()) or cfg.sha(path)!=digest: raise ValueError("Bundle source changed")
        config=cfg.transform(json.loads((bundle/"config.json").read_text()),lambda text:text.replace("@BUNDLE@",str(bundle)).replace("@PDK@",os.environ["PDK_ROOT"]))
        if config.get("MAX_FANOUT_CONSTRAINT")!=10 or config["CLOCK_PERIOD"]!=20 or config["STA_CORNERS"]!=list(CORNERS): raise ValueError("Original constraints differ")
        if config.get("PAD_LIBS") is None:config["PAD_LIBS"]={}
        config["CTS_SINK_CLUSTERING_SIZE"]=8
        config["meta"]={"version":2,"flow":["OpenROAD.STAMidPNR"]}
        (OUT/"config.json").write_text(json.dumps(config,indent=2))
        script=OUT/"padding.tcl";script.write_text(cfg.CENSUS+EDIT)
        env={"WARP_INPUT_ODB":baseline["odb"],"WARP_BEFORE":OUT/"before.tsv","WARP_AFTER":OUT/"after.tsv",
             "WARP_GEOMETRY_BEFORE":OUT/"geometry_before.tsv","WARP_GEOMETRY_AFTER":OUT/"geometry_after.tsv",
             "WARP_SELECTION":OUT/"selected.txt","WARP_OUTPUT_ODB":OUT/"padded.odb","WARP_OUTPUT_NL":OUT/"padded.nl.v"}
        command=["docker","run","--rm","-v",f"{ROOT}:{ROOT}","-w",str(ROOT)]
        for key,value in env.items():command.extend(["-e",f"{key}={value}"])
        command.extend(["--entrypoint","openroad",cfg.IMAGE,"-exit",str(script)])
        with (OUT/"padding.log").open("w") as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        before=(OUT/"before.tsv").read_text()
        if cfg.parse_census(before)!=cfg.parse_census((source/"after.tsv").read_text()):raise ValueError("Native baseline census differs from authenticated source")
        result["placement"]=audit_placement(before,(OUT/"after.tsv").read_text(),(OUT/"geometry_before.tsv").read_text(),(OUT/"geometry_after.tsv").read_text(),(OUT/"selected.txt").read_text().splitlines())
        result["candidate_sha256"]={"odb":cfg.sha(OUT/"padded.odb"),"nl":cfg.sha(OUT/"padded.nl.v")};save()
        for label,odb,nl in (("baseline",baseline["odb"],baseline["nl"]),("padded",OUT/"padded.odb",OUT/"padded.nl.v")):
            for corner in CORNERS:
                result[label+"_sta_"+corner]=sta(config,label+"_sta_"+corner,odb,nl,baseline["sdc"],corner);save()
        authenticate_views(baseline,BUFFERED)
        result["authenticated_sources_unchanged"]=True;result["passed"]=True
    except Exception as exc:
        result["error"]=str(exc);raise
    finally:save()


if __name__=="__main__":main()

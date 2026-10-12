"""Horizontal mirroring on exact combined placement; fixed physical bboxes.

Copied checkpoint only. Native legality, power phase, connectivity, source
control and six electrical guards precede any routing/physical acceptance.
"""
import json
import os
from pathlib import Path

import cloud_reset_combined as combo
import cloud_hotspot_padding as producer
import cloud_cfg_fanout as cfg

ROOT = cfg.ROOT
INPUT = ROOT / "build/pin_mirror_input"
OUT = ROOT / "build/pin_mirror"


def edit():
    source = combo.trial.edit()
    anchor = "write_db $::env(WARP_OUTPUT_ODB)"
    if source.count(anchor) != 1:
        raise ValueError("Nonunique write anchor")
    injection = r"""
census ${::env(WARP_AFTER)}.mirror_control
geometry ${::env(WARP_GEOMETRY_AFTER)}.mirror_control
if {[llength [info commands optimize_mirroring]] != 1} {error "Pinned mirroring command absent"}
optimize_mirroring
check_placement -verbose
census $::env(WARP_AFTER)
geometry $::env(WARP_GEOMETRY_AFTER)
"""
    return source.replace(anchor, injection + anchor)


def audit(before, after, geometry_before, geometry_after, selected):
    control = (OUT / "after.tsv.mirror_control").read_text()
    cg = (OUT / "geometry_after.tsv.mirror_control").read_text()
    replay = combo.trial.audit_move(before,control,geometry_before,cg,selected)
    expected = INPUT / "combined"
    if (cfg.parse_census(control)!=cfg.parse_census((expected/"after.tsv").read_text())
            or producer.boxes(cg)!=producer.boxes((expected/"geometry_after.tsv").read_text())
            or cfg.sha(expected/"result.json")!="28739ad6b5379ef6ed299d1b5c613b577c8059be9807a3e407c179dca74a48cb"):
        raise ValueError("Actual133 control differs")
    old,opins = cfg.parse_census(control)
    new,npins = cfg.parse_census(after)
    if set(old)!=set(new) or opins!=npins or producer.boxes(cg)!=producer.boxes(geometry_after):
        raise ValueError("Mirroring changes topology or physical bboxes")
    boxes = producer.boxes(cg)[2]
    changed = []
    for name in old:
        a,b = old[name],new[name]
        if a[0]!=b[0] or a[3:]!=b[3:]:
            raise ValueError("Master/status differs: "+name)
        if a!=b:
            if (boxes[name][0]!="CORE" or a[3]!="PLACED" or a[2]==b[2]
                    or not producer.same_vertical_phase(a[2],b[2])):
                raise ValueError("Unexpected nonhorizontal/fixed change: "+name)
            changed.append({"instance":name,"before_orientation":a[2],"after_orientation":b[2]})
    return {"combined_control_replay":replay,"all_bboxes_exact":True,
        "masters_connectivity_status_exact":True,"vertical_power_phase_exact":True,
        "horizontal_mirrors":changed,"mirror_count":len(changed),
        "routing_benefit_unproven":True}


def main():
    if os.environ.get("GITHUB_ACTIONS")!="true":
        raise ValueError("Native mirroring is cloud only")
    producer.INPUT,producer.OUT = INPUT,OUT
    producer.EDIT,producer.audit_placement = edit(),audit
    try:
        producer.main()
    finally:
        path=OUT/"result.json"
        if path.exists():
            result=json.loads(path.read_text())
            result["scope"]="Horizontal mirroring of combined133 placement; all bboxes fixed"
            path.write_text(json.dumps(result,indent=2)+"\n")


if __name__=="__main__":main()

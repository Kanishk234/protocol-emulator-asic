"""Compare the authenticated133-overflow control with measured smaller delays."""
import json
import math
from pathlib import Path
import shutil
import cloud_hold_allocation as control
import cloud_delay_rebalance as producer
import cloud_cfg_fanout as cfg
import cloud_hotspot_grt as paired

ROOT = cfg.ROOT
INPUT = ROOT / "build/delay_rebalance_grt_input"
OUT = ROOT / "build/delay_rebalance_grt"
PRODUCER_SHA = "dd19fa05fd4c46c71d74daa73f371edf2dac439e3bf11e61f3f029a49eebdb8e"
SDC_SHA = "2fd4e213532d83ee258899b6fc1ed48c4e5d91ddb0ccbe21eea0226cc90fd56e"
BASELINE = {"odb":control.EXPECTED["padded.odb"],"nl":control.EXPECTED["padded.nl.v"],"sdc":SDC_SHA}
CANDIDATE = {"odb":"d213774b48b5a3ef93f529228bbb5e9a7b95e54419bdd3bc6602552adfc2c948",
             "nl":"1a2bc7db166798abb6c83a664e589bcf028110ab4267b922a11890a7da52d858","sdc":SDC_SHA}


def validate_control(directory):
    for name,digest in control.EXPECTED.items():
        if cfg.sha(directory/name)!=digest: raise ValueError("Best control differs")
    if cfg.sha(directory/"result.json") != "28739ad6b5379ef6ed299d1b5c613b577c8059be9807a3e407c179dca74a48cb":
        raise ValueError("Control producer differs")
    for name,key in (("buffered.odb","odb"),("buffered.nl.v","nl")):
        if cfg.sha(directory/name)!=BASELINE[key]:raise ValueError("Control routing view differs")


def validate_producer(directory, baseline):
    validate_control(baseline)
    if cfg.sha(directory/"result.json")!=PRODUCER_SHA:raise ValueError("Measured delay producer differs")
    result=json.loads((directory/"result.json").read_text())
    if (result.get("producer_passed") is not True or result.get("source_run")!=38167697696
            or result.get("timing_source_run")!=38315257114):raise ValueError("Wrong/unqualified delay producer")
    evidence=INPUT/"timing/result.json"
    if cfg.sha(evidence)!=producer.EVIDENCE_SHA:raise ValueError("Selection evidence differs")
    selected=producer.select(json.loads(evidence.read_text()))
    if set((directory/"selected.txt").read_text().splitlines())!=selected:raise ValueError("Measured selection differs")
    measured=producer.audit_change((baseline/"after.tsv").read_text(),(directory/"after.tsv").read_text(),
        (baseline/"geometry_after.tsv").read_text(),(directory/"geometry_after.tsv").read_text(),selected)
    if measured!=result["audit"]:raise ValueError("Actual geometry audit differs")
    for name,key in (("padded.odb","odb"),("padded.nl.v","nl")):
        if cfg.sha(directory/name)!=CANDIDATE[key]:raise ValueError("Measured candidate view differs")
    for corner in ("nom_fast_1p32V_m40C","nom_typ_1p20V_25C","nom_slow_1p08V_125C"):
        case=result["corners"][corner];metrics=case["metrics"]
        if case["odb_sha256"]!=CANDIDATE["odb"] or case["nl_sha256"]!=CANDIDATE["nl"] or case["sdc_sha256"]!=SDC_SHA:
            raise ValueError("Measured timing views differ")
        for kind in ("setup","hold"):
            slack=metrics[f"timing__{kind}__ws__corner:{corner}"]
            if not isinstance(slack,(int,float)) or not math.isfinite(slack) or slack<=0 or metrics[f"timing__{kind}_vio__count__corner:{corner}"]!=0:
                raise ValueError("Producer timing gate failed")
        if metrics[f"timing__hold__ws__corner:{corner}"]<0.1:raise ValueError("Producer hold guard failed")
        for kind in ("max_fanout","max_slew","max_cap"):
            if metrics[f"design__{kind}_violation__count__corner:{corner}"]!=0:raise ValueError("Producer electrical gate failed")
    return measured


def main():
    baseline,candidate=INPUT/"baseline",INPUT/"padded"
    for name,digest in control.EXPECTED.items():
        if cfg.sha(baseline/name)!=digest:raise ValueError("Original control differs before adaptation")
    archive=ROOT/"build/fanout-preflight-source.tar.gz"
    if cfg.sha(archive)!=cfg.SOURCE_SHA:raise ValueError("Original payload archive differs")
    control.prepare_payload(archive,baseline/"original_source")
    # Only adapter file names change; source bytes and real physical views do not.
    for directory,old,new in ((baseline,"padded.odb","buffered.odb"),(baseline,"padded.nl.v","buffered.nl.v"),
            (candidate,"candidate.odb","padded.odb"),(candidate,"candidate.nl.v","padded.nl.v")):
        shutil.copyfile(directory/old,directory/new)
    sdc=baseline/"padded_sta_nom_typ_1p20V_25C/final/sdc/tt_um_warp.sdc"
    target=baseline/"buffered_sta_nom_typ_1p20V_25C/final/sdc/tt_um_warp.sdc"
    target.parent.mkdir(parents=True,exist_ok=False);shutil.copyfile(sdc,target)
    shutil.copyfile(baseline/"after.tsv",candidate/"before.tsv")
    (candidate/"original_source").symlink_to(baseline/"original_source",target_is_directory=True)
    paired.INPUT,paired.OUT=INPUT,OUT
    paired.SOURCE_RUN,paired.RESULT_SHA=38316322592,PRODUCER_SHA
    paired.BUFFERED,paired.PADDED=BASELINE,CANDIDATE
    paired.validate_candidate,paired.validate_padding=validate_control,validate_producer
    try:
        paired.main()
    finally:
        path=OUT/"result.json"
        if path.exists():
            result=json.loads(path.read_text())
            result["source_runs"]["baseline"]=38167697696
            result["scope"]="unchanged-policy paired GRT: best133 control versus measured251-cell delay rebalance"
            result["candidate_global_route_passed"]=result.get("cases",{}).get("padded",{}).get("route_passed",False)
            path.write_text(json.dumps(result,indent=2)+"\n")


if __name__=="__main__":main()

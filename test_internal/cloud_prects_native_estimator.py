"""D-094: replace the failed RUDY proxy with native routing feedback in placement."""
import json
import os
from pathlib import Path
import subprocess
import sys
import cloud_prects_reflow as trial
import cloud_cfg_fanout as cfg

ROOT=cfg.ROOT
OUT=ROOT/'build/prects_native_estimator'
GPL_SHA='b293515d3bf5ac4bdd45498f9de9d842926f16eeb078c78ec48bfc683dffb547'
ANCHOR='log_cmd global_placement {*}$arg_list'
INSERT='lappend arg_list -routability_use_grt\n'
ORIGINAL_STAGE=trial.run_stage


def instrument(original,directory):
    if cfg.sha(original)!=GPL_SHA:raise ValueError('Pinned global-placement Tcl differs')
    text=original.read_text()
    if text.count(ANCHOR)!=1:raise ValueError('Nonunique placement-command anchor')
    directory.mkdir(exist_ok=False)
    copied=directory/'gpl-native-estimator.tcl'
    copied.write_text(text.replace(ANCHOR,INSERT+ANCHOR,1))
    if copied.read_text().replace(INSERT,'',1)!=text:raise ValueError('Unexpected upstream-script change')
    (directory/'ATTRIBUTION.md').write_text('Copied from pinned LibreLane3.1.0.dev3, Apache2.0. Original copyright/license headers retained. Upstream installed source is untouched. D094 adds only -routability_use_grt before global_placement.\n')
    (directory/'source-sha256.json').write_text(json.dumps({'original':GPL_SHA,'copied':cfg.sha(copied),
        'only_change':'placement congestion estimator RUDY to native FastRoute; final routing gates unchanged'},indent=2)+'\n')
    return copied


def inside(config,state,run):
    from librelane.flows import SequentialFlow
    from librelane.state import State
    from librelane.steps import OpenROAD
    class NativeGPL(OpenROAD.GlobalPlacement):
        def get_script_path(self):
            if not hasattr(self,'_native_script'):
                self._native_script=str(instrument(Path(super().get_script_path()),run/'placement-source'))
            return self._native_script
    class Comparison(SequentialFlow):
        Steps=[NativeGPL,OpenROAD.DetailedPlacement,OpenROAD.CTS,OpenROAD.ResizerTimingPostCTS,OpenROAD.STAMidPNR]
    flow=Comparison(str(config),design_dir=str(ROOT),pdk='ihp-sg13cmos5l',pdk_root=os.environ['PDK_ROOT'])
    flow.start(with_initial_state=State.loads(state.read_text()),_force_run_dir=str(run))


def dispatch(config,state,label):
    if label!='reflow':return ORIGINAL_STAGE(config,state,label)
    path=OUT/(label+'_config.json');path.write_text(json.dumps(config))
    initial=OUT/(label+'_state.json');initial.write_text(json.dumps(state))
    run=OUT/label;run.mkdir(exist_ok=False)
    cmd=['docker','run','--rm','-v',f'{ROOT}:{ROOT}','-w',str(ROOT),'-e',f"PDK_ROOT={os.environ['PDK_ROOT']}",
        '--entrypoint','python3',cfg.IMAGE,str(Path(__file__).resolve()),'--inside',str(path),str(initial),str(run)]
    with (OUT/(label+'.log')).open('w') as log:
        subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1200)
    # Fail closed if the advertised estimator flag never reached native execution.
    stage,=run.glob('*-openroad-globalplacement')
    resolved=json.loads((stage/'config.json').read_text())
    for key in ('RT_MIN_LAYER','RT_MAX_LAYER','GRT_ADJUSTMENT','GRT_LAYER_ADJUSTMENTS','GRT_MACRO_EXTENSION'):
        if resolved.get(key)!=config.get(key):raise ValueError('Placement routing policy changed: '+key)
    raw=(stage/'openroad-globalplacement.log').read_text()
    commands=[line for line in raw.splitlines() if line.startswith('+ global_placement ')]
    if not commands or any('-routability_use_grt' not in line for line in commands):
        raise ValueError('Actual native estimator flag missing')
    return run


def main():
    trial.OUT=OUT;trial.run_stage=dispatch
    try:trial.main()
    finally:
        path=OUT/'result.json'
        if path.exists():
            result=json.loads(path.read_text());result['scope']='before-CTS native routing-estimator comparison; final electrical/timing/routing gates not waived'
            result['estimator']='native FastRoute';result['original_gpl_sha256']=GPL_SHA
            path.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    if len(sys.argv)==5 and sys.argv[1]=='--inside':inside(*map(Path,sys.argv[2:]))
    elif len(sys.argv)==1:main()
    else:raise SystemExit('Unsupported invocation')

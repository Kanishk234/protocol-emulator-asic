"""Read-only VPI replay of BUG163; instrumented results never qualify timing."""
import argparse
import json
import os
from pathlib import Path

from assembly_catalog import sha
from configured_smoke import run as smoke


def run(out,pdk,icarus,watchdog):
    if os.environ.get('GITHUB_ACTIONS')!='true':
        raise ValueError('Heavy native diagnosis runs hosted')
    out,pdk,icarus,watchdog=(Path(p).resolve() for p in (out,pdk,icarus,watchdog))
    plan=json.loads((out/'plan.json').read_text())
    if plan['trial_kind']!='fixed_relocation':raise ValueError('Require the original stalled relocation trial')
    if any(sha(p)!=h for p,h in plan['input_sha256'].items()):
        raise ValueError('Frozen diagnostic inputs changed')
    if watchdog.suffix!='.vpi' or not watchdog.is_file():raise ValueError('Missing VPI observer')
    # Interpose only in this isolated diagnostic process, leaving the acceptance
    # runner unchanged. The observer registers callbacks and never drives nets.
    import cocotb_tools.runner as runners
    original=runners.get_runner
    def observed_runner(name):
        runner=original(name);test=runner.test
        def observed_test(*args,**kwargs):
            kwargs['test_args']=[*kwargs.get('test_args',[]),'-m',str(watchdog.with_suffix(''))]
            return test(*args,**kwargs)
        runner.test=observed_test
        return runner
    runners.get_runner=observed_runner
    os.environ['R1_RUNTIME_MODEL']=plan['native']
    os.environ['WARP_DELTA_START_TICKS']='0'
    cap=Path(plan['capsule'])
    result=dict(run=os.environ.get('GITHUB_RUN_ID'),source_sha=os.environ.get('GITHUB_SHA'),
                diagnostic_complete=False,passed=False,timing_acceptance=False,physical_acceptance=False,
                adopted=False,watchdog_sha256=sha(watchdog),
                observer_source_sha256=sha(Path(__file__).with_name('delta_watchdog.c')),
                scope='Instrumented native replay only. An observer stop or missing XML remains a failure. No forced values or added circuit delays.',cases={})
    try:
        for stage in ('control','candidate'):
            try:
                smoke(cap/'model/resource',out/(stage+'-case'),out/('delta-'+stage),
                      pdk=pdk,icarus_root=icarus,mapped_bundle=cap/'mapped/input',
                      postphysical_complete=out/'native-audit.json',capture_configuration=True,
                      quiesce_unused=True,restart_probe=True)
                result['cases'][stage]=dict(instrumented_test_passed=True)
            except (Exception,SystemExit) as exc:
                result['cases'][stage]=dict(instrumented_test_passed=False,error=str(exc))
                if stage=='control':raise ValueError('Instrumented original control failed') from exc
        result['diagnostic_complete']=True
    finally:
        runners.get_runner=original
        (out/'delta-result.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('out','pdk','icarus','watchdog'):parser.add_argument('--'+name,type=Path,required=True)
    run(**vars(parser.parse_args()))

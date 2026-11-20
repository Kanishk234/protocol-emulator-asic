"""Connected RC diagnostic for actually loaded placement images; no acceptance."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

from assembly_catalog import sha
from compile.bitfile import BitFile
from configuration_audit import audit
from routed_timing import annotation,assert_cases,observed_cases,prepare as prepare_parent,run as run_parent
from run_timing import compare,parse_log


def replace_cases(text,old,new):
    assert_cases(text,old)
    if set(new)!=set(old) or any(v not in ('0','1') for v in new.values()):
        raise ValueError('Candidate configuration identity or binary state differs')
    pattern=(r'(set p \[get_pins -quiet \{([^{}]+/Q)\}\]\n'
             r'if \{\[llength \$p\]!=1\} \{error "missing configuration pin"\}\n'
             r'set_case_analysis )([01])( \$p\nincr observed)')
    result=re.sub(pattern,lambda m:m[1]+new[m[2]]+m[4],text)
    assert_cases(result,new)
    return result


def prepare(rc,proof,native,capsule,pdk,functional,out):
    functional,out=Path(functional).resolve(),Path(out).resolve()
    data=json.loads((functional/'result.json').read_text())
    if (not data['passed'] or not {'control','candidate','shell'}<=set(data['cases']) or
            any(not row['passed'] for row in data['cases'].values())):
        raise ValueError('Require all actual native loading cases')
    if data['cases']['candidate']!=data['cases']['shell']:
        raise ValueError('Actual direct and management/reload observations differ')
    observed=json.loads((functional/'candidate/configuration-state.json').read_text())
    image=functional/'candidate/quiesced.wbit'
    quiescence=json.loads((functional/'candidate/quiescence.json').read_text())
    admitted={'0834b13c09e5e23a35122f71258ceabfbe8a61d3dffbc31b6b0a1851921d241f',
              'cf186c6d78f4b003ffc868b3f6d5e34f16aad4e1df14f2989195dbd03a7d049b',
              'cbea6b084f843d95222cbb93cfd4a55ac0698a3d51b54689eb358d9678ff0462'}
    if quiescence['source_image_sha256'] not in admitted:
        raise ValueError('Require an admitted fixed-source placement image')
    if sha(image)!=data['cases']['candidate']['image_sha256'] or sha(functional/'candidate/configuration-state.json')!=data['cases']['candidate']['observed_configuration_sha256']:
        raise ValueError('Actual native evidence changed')
    modules=Path(native)/'registered_native/all-native.json'
    frame=audit(json.loads(modules.read_text())['modules'],observed,BitFile.load(image).words)
    if not frame['passed'] or frame['compared_configuration_bits']!=8736:
        raise ValueError('Actual SA frame agreement incomplete')
    out.mkdir(parents=True,exist_ok=False)
    prepare_parent(rc,proof,native,capsule,pdk,out/'baseline')
    old=observed_cases(json.loads((Path(native)/'registered_functional/candidate/configuration-state.json').read_text()))
    new=observed_cases(observed);scripts={}
    for kind in ('setup','hold'):
        for policy in ('static','dynamic'):
            label='routed_'+kind+'_'+policy
            target=out/(label+'.tcl')
            target.write_text(replace_cases((out/'baseline'/(label+'.tcl')).read_text(),old,new))
            scripts[label]=sha(target)
    bound=[Path(__file__).resolve(),functional/'result.json',functional/'candidate/configuration-state.json',image,
           functional/'candidate/quiescence.json',modules]
    (out/'plan.json').write_text(json.dumps(dict(inputs={str(p):sha(p) for p in bound},scripts=scripts,
         actual_native_run=data['run'],frame_audit=frame,actually_loaded_image_sha256=sha(image)),indent=2)+'\n')


def run(out):
    out=Path(out).resolve();plan=json.loads((out/'plan.json').read_text())
    if any(sha(p)!=h for p,h in plan['inputs'].items()):raise ValueError('Actual candidate evidence changed')
    try:run_parent(out/'baseline')
    except SystemExit:pass
    parent=json.loads((out/'baseline/result.json').read_text())
    if not parent['diagnostic_complete'] or parent.get('error')!='Configured macro setup/hold or loop-policy check fails':
        raise ValueError('Original connected timing control did not reproduce')
    if any(not a['passed'] for k,a in parent['annotation'].items() if k.startswith('routed_')):
        raise ValueError('Original active annotation is incomplete')
    models={};coverage={}
    for kind in ('setup','hold'):
        logs=[]
        for policy in ('static','dynamic'):
            label='routed_'+kind+'_'+policy;script=out/(label+'.tcl')
            if sha(script)!=plan['scripts'][label]:raise ValueError('SA case script changed')
            with (out/(label+'.log')).open('w') as stream:
                proc=subprocess.run(['sta','-exit',str(script)],stdout=stream,stderr=subprocess.STDOUT,timeout=240)
            if proc.returncode:raise ValueError('Native SA timing execution failed')
            text=(out/(label+'.log')).read_text();logs.append(parse_log(text));coverage[label]=annotation(text)
        models[kind]=compare(*logs)
    qualified=all(a['passed'] for a in coverage.values()) and all(not m['loop_policy_sensitive'] and m['structural_loops']==0 for m in models.values())
    result=dict(run=os.environ.get('GITHUB_RUN_ID'),source_sha=os.environ.get('GITHUB_SHA'),diagnostic_complete=True,
        models=models,coverage=coverage,model_qualified=qualified,
        necessary_macro_constraints_met=qualified and all(m['worst_slack_ns']>=0 for m in models.values()),
        actual_native_run=plan['actual_native_run'],actually_loaded_image_sha256=plan['actually_loaded_image_sha256'],
        timing_acceptance=False,physical_acceptance=False,adopted=False,
        scope='Actually loaded placement image on unchanged source-proven connected nominal RC, original 20ns/0.25ns/conditional zero-I/O boundary. Original failing parent retained. No full-chip/PVT/loading-mode acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    if not qualified:raise SystemExit('SA timing model coverage/loop qualification failed; retain failure')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('prepare')
    for name in ('rc','proof','native','capsule','pdk','functional','out'):p.add_argument('--'+name,type=Path,required=True)
    sub.add_parser('run').add_argument('--out',type=Path,required=True)
    args=vars(parser.parse_args());mode=args.pop('mode');(prepare if mode=='prepare' else run)(**args)

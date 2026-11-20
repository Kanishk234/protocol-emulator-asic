"""Actually load the fixed-seed SA image into all forty native tiles."""
import argparse
import json
import os
from pathlib import Path
import shutil

from assembly_catalog import sha
from configuration_audit import audit
from configured_smoke import complete_native_exports, run as smoke
from compile.bitfile import BitFile


def prepare(capsule,native,trial,out):
    capsule,native,trial,out=(Path(p).resolve() for p in (capsule,native,trial,out))
    result=json.loads((trial/'result.json').read_text())
    if (result['run']!='44653541979' or not result['diagnostic_complete'] or
        result['cases']['candidate']['image_sha256']!='0834b13c09e5e23a35122f71258ceabfbe8a61d3dffbc31b6b0a1851921d241f'):
        raise ValueError('Require the authenticated fixed-seed SA trial')
    out.mkdir(parents=True,exist_ok=False)
    control=json.loads((capsule/'leaf-audit.json').read_text())
    for row in control['native_exports'].values():
        suffix=row['path'].split('/build/r1_timing/',1)[1];path=capsule/suffix
        if not path.resolve().is_relative_to(capsule) or sha(path)!=row['sha256']:
            raise ValueError('Native source export changed')
        row['path']=str(path)
    (out/'native-audit.json').write_text(json.dumps(control,indent=2)+'\n')
    complete_native_exports(out/'native-audit.json')
    for name in ('control','candidate'):
        dest=out/(name+'-case');dest.mkdir()
        for filename in ('report.json','design.fasm','concurrency.wbit'):
            shutil.copyfile(trial/name/filename,dest/filename)
        if sha(dest/'concurrency.wbit')!=result['cases'][name]['image_sha256']:
            raise ValueError('Compiled image changed')
    modules=native/'registered_native/all-native.json'
    if sha(modules)!='64922d92969e229e8562d9cc0c4bd1cb5add15766ec10709576f0255ebf2ce06':
        raise ValueError('Native frame audit source changed')
    (out/'plan.json').write_text(json.dumps(dict(capsule=str(capsule),native=str(modules),
        input_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),trial/'result.json',modules,out/'native-audit.json',
          *[out/(n+'-case')/f for n in ('control','candidate') for f in ('report.json','design.fasm','concurrency.wbit')]]}),indent=2)+'\n')


def run(out,pdk,icarus):
    if os.environ.get('GITHUB_ACTIONS')!='true':raise ValueError('Native candidate simulation runs hosted')
    if os.environ.get('R1_REGISTERED_INPUT_EXPERIMENT'):raise ValueError('No inherited parent-specific bit repair')
    out,pdk,icarus=(Path(p).resolve() for p in (out,pdk,icarus))
    plan=json.loads((out/'plan.json').read_text())
    if any(sha(p)!=h for p,h in plan['input_sha256'].items()):raise ValueError('Frozen functional input changed')
    cap=Path(plan['capsule']);modules=json.loads(Path(plan['native']).read_text())['modules']
    os.environ['R1_RUNTIME_MODEL']=plan['native']
    result=dict(run=os.environ.get('GITHUB_RUN_ID'),source_sha=os.environ.get('GITHUB_SHA'),passed=False,
                cases={},timing_acceptance=False,physical_acceptance=False,adopted=False)
    try:
        for stage,name,shell in [('control','control',False),('candidate','candidate',False),('shell','candidate',True)]:
            smoke(cap/'model/resource',out/(name+'-case'),out/stage,
                pdk=pdk,icarus_root=icarus,mapped_bundle=cap/'mapped/input',
                postphysical_complete=out/'native-audit.json',capture_configuration=True,
                management_shell=shell,quiesce_unused=True,restart_probe=not shell)
            proof=json.loads((out/stage/'configured-smoke.json').read_text())
            image=BitFile.load(out/stage/'quiesced.wbit')
            state=json.loads((out/stage/'configuration-state.json').read_text())
            frame=audit(modules,state,image.words)
            if not proof['passed'] or not frame['passed'] or frame['compared_configuration_bits']!=8736:
                raise ValueError('Incomplete actual native loading/frame evidence')
            (out/stage/'frame-audit.json').write_text(json.dumps(frame,indent=2)+'\n')
            result['cases'][stage]=dict(passed=True,image_sha256=sha(out/stage/'quiesced.wbit'),
                observed_configuration_sha256=sha(out/stage/'configuration-state.json'),configuration_bits=8736)
            (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        if result['cases']['candidate']!=result['cases']['shell']:
            raise ValueError('Direct and management/reload native observations differ')
        result['passed']=True
    except Exception as exc:
        result['error']=str(exc)
        if stage=='candidate':
            try:
                smoke(cap/'model/resource',out/'candidate-case',out/'generated-rtl',
                    quiesce_unused=True,restart_probe=True)
                result['generated_rtl_candidate']=dict(passed=True,
                    scope='Generated RTL diagnostic only; original native failure retained.')
            except Exception as rtl_error:
                result['generated_rtl_candidate']=dict(passed=False,error=str(rtl_error))
        raise
    finally:(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('prepare')
    for name in ('capsule','native','trial','out'):p.add_argument('--'+name,type=Path,required=True)
    p=sub.add_parser('run')
    for name in ('out','pdk','icarus'):p.add_argument('--'+name,type=Path,required=True)
    args=vars(parser.parse_args());mode=args.pop('mode');(prepare if mode=='prepare' else run)(**args)

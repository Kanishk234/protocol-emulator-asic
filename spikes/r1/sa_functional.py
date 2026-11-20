"""Actually load admitted placement images into all forty native tiles."""
import argparse
import json
import os
from pathlib import Path
import shutil

from assembly_catalog import sha
from configuration_audit import audit
from configured_smoke import complete_native_exports, run as smoke
from compile.bitfile import BitFile


def prepare(capsule,native,trial,out,trial_kind='sa'):
    capsule,native,trial,out=(Path(p).resolve() for p in (capsule,native,trial,out))
    trial_inputs=[trial/'result.json']
    if trial_kind=='spi_timer_free_run':
        trial_inputs=[trial/name/'result.json' for name in ('control','candidate')]
        cases={name:json.loads(path.read_text()) for name,path in zip(('control','candidate'),trial_inputs)}
        if any(str(row['run'])!='44798802734' or row['source_sha']!='693e3b6bee9d082109c616431648646693c0a4be' or
               row['actual_native_loading'] or row['model_timing_characterized'] for row in cases.values()):
            raise ValueError('Require the authenticated source-proven SPI compile campaign')
        if cases['control']['image_sha256']!='c6b96ef02d052b405f58b9742acbff02c0fd0c4e31f6d278e09649d1a5e6991f':
            raise ValueError('Original compiler control did not reproduce')
        result=dict(run='44798802734',diagnostic_complete=True,cases=cases)
    else:result=json.loads(trial_inputs[0].read_text())
    admitted={
        'sa':('44653541979','0834b13c09e5e23a35122f71258ceabfbe8a61d3dffbc31b6b0a1851921d241f'),
        'fixed_relocation':('44676960615','cf186c6d78f4b003ffc868b3f6d5e34f16aad4e1df14f2989195dbd03a7d049b'),
        'fixed_reroute':('44676960615','cbea6b084f843d95222cbb93cfd4a55ac0698a3d51b54689eb358d9678ff0462'),
        'spi_timer_free_run':('44798802734','79db28f92959f998faf2b6b00b65be3539abc5e03625f77bd80584601fa2fd6a'),
        'spi_clock_d':('44827334401','4326eab8868442494239e0a413aa199158293b14cff856453ae8c37bd6d7403a')}
    if trial_kind not in admitted:raise ValueError('Unknown fixed-source native trial')
    run_id,image_sha=admitted[trial_kind]
    if (str(result['run'])!=run_id or not result['diagnostic_complete'] or
        result['cases']['reroute' if trial_kind=='fixed_reroute' else 'candidate']['image_sha256']!=image_sha):
        raise ValueError('Require the authenticated fixed-source placement trial')
    if trial_kind=='spi_clock_d':
        if (result['cases']['control']['image_sha256']!='79db28f92959f998faf2b6b00b65be3539abc5e03625f77bd80584601fa2fd6a' or
                any(not row['logical_graph_preserved'] for row in result['cases'].values()) or
                result['cases']['control']['clock_bank']!='X0Y4/A' or result['cases']['candidate']['clock_bank']!='X0Y4/D' or
                result['cases']['control']['placed_utilisation']!=result['cases']['candidate']['placed_utilisation']):
            raise ValueError('Clock-bank source, graph or resource control changed')
    case_names={'control':'restore' if trial_kind in ('fixed_relocation','fixed_reroute') else 'control',
                'candidate':'reroute' if trial_kind=='fixed_reroute' else 'candidate'}
    if trial_kind in ('fixed_relocation','fixed_reroute'):
        if trial_kind=='fixed_relocation':case_names['reroute']='reroute'
        if any(not r['logical_graph_preserved'] or not r['placements_exact'] for r in result['cases'].values()):
            raise ValueError('Fixed-placement graph/source checks failed')
    out.mkdir(parents=True,exist_ok=False)
    control=json.loads((capsule/'leaf-audit.json').read_text())
    for row in control['native_exports'].values():
        suffix=row['path'].split('/build/r1_timing/',1)[1];path=capsule/suffix
        if not path.resolve().is_relative_to(capsule) or sha(path)!=row['sha256']:
            raise ValueError('Native source export changed')
        row['path']=str(path)
    (out/'native-audit.json').write_text(json.dumps(control,indent=2)+'\n')
    complete_native_exports(out/'native-audit.json')
    for name,source_name in case_names.items():
        dest=out/(name+'-case');dest.mkdir()
        for filename in ('report.json','design.fasm','concurrency.wbit'):
            shutil.copyfile(trial/source_name/filename,dest/filename)
        if sha(dest/'concurrency.wbit')!=result['cases'][source_name]['image_sha256']:
            raise ValueError('Compiled image changed')
    modules=native/'registered_native/all-native.json'
    if sha(modules)!='64922d92969e229e8562d9cc0c4bd1cb5add15766ec10709576f0255ebf2ce06':
        raise ValueError('Native frame audit source changed')
    (out/'plan.json').write_text(json.dumps(dict(capsule=str(capsule),native=str(modules),trial_kind=trial_kind,
        input_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),*trial_inputs,modules,out/'native-audit.json',
          *[out/(n+'-case')/f for n in case_names for f in ('report.json','design.fasm','concurrency.wbit')]]}),indent=2)+'\n')


def run(out,pdk,icarus):
    if os.environ.get('GITHUB_ACTIONS')!='true':raise ValueError('Native candidate simulation runs hosted')
    if os.environ.get('R1_REGISTERED_INPUT_EXPERIMENT'):raise ValueError('No inherited parent-specific bit repair')
    out,pdk,icarus=(Path(p).resolve() for p in (out,pdk,icarus))
    plan=json.loads((out/'plan.json').read_text())
    if any(sha(p)!=h for p,h in plan['input_sha256'].items()):raise ValueError('Frozen functional input changed')
    cap=Path(plan['capsule']);modules=json.loads(Path(plan['native']).read_text())['modules']
    os.environ['R1_RUNTIME_MODEL']=plan['native']
    result=dict(run=os.environ.get('GITHUB_RUN_ID'),source_sha=os.environ.get('GITHUB_SHA'),passed=False,
                cases={},trial_kind=plan.get('trial_kind','sa'),timing_acceptance=False,physical_acceptance=False,adopted=False)
    try:
        stages=[('control','control',False)]
        if plan.get('trial_kind')=='fixed_relocation':stages.append(('reroute','reroute',False))
        stages += [('candidate','candidate',False),('shell','candidate',True)]
        for stage,name,shell in stages:
            try:
                smoke(cap/'model/resource',out/(name+'-case'),out/stage,
                    pdk=pdk,icarus_root=icarus,mapped_bundle=cap/'mapped/input',
                    postphysical_complete=out/'native-audit.json',capture_configuration=True,
                    management_shell=shell,quiesce_unused=True,restart_probe=not shell)
            except Exception as exc:
                if stage!='reroute':raise
                result['cases']['reroute']=dict(passed=False,error=str(exc))
                continue
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
        result['candidate_functional_passed']=True
        result['passed']=all(row['passed'] for row in result['cases'].values())
        if not result['passed']:raise ValueError('Reroute control failed; candidate evidence retained separately')
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
    p.add_argument('--trial-kind',choices=('sa','fixed_relocation','fixed_reroute','spi_timer_free_run','spi_clock_d'),default='sa')
    p=sub.add_parser('run')
    for name in ('out','pdk','icarus'):p.add_argument('--'+name,type=Path,required=True)
    args=vars(parser.parse_args());mode=args.pop('mode');(prepare if mode=='prepare' else run)(**args)

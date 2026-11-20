"""Bounded real-image tests of cofactor-proved SA constant-LUT inputs."""
import argparse
import copy
import io
import json
import os
from pathlib import Path
import shutil

from assembly_catalog import sha
from compile.bitfile import BitFile
from compile.bitgen import fasm_features
from configuration_audit import audit
from configured_smoke import complete_native_exports,run as smoke
from profiling.r1_quiesce import PlainSpec
from unused_input_sweep import prove_input,carry_modes

TARGETS=(('X5Y1','C',0),('X5Y1','F',0),('X5Y1','F',3))


def prepare(capsule,native,functional,out):
    capsule,native,functional,out=(Path(p).resolve() for p in (capsule,native,functional,out))
    parent=functional/'candidate';case=functional/'candidate-case'
    data=json.loads((functional/'result.json').read_text())
    if (str(data['run'])!='44673352765' or data['source_sha']!='def28bcd47386e31659238fb93263df46cb771e3' or
            data['passed'] or not data['cases']['control']['passed'] or not data['generated_rtl_candidate']['passed']):
        raise ValueError('Require retained native failure and passing original/RTL controls')
    if sha(case/'concurrency.wbit')!='0834b13c09e5e23a35122f71258ceabfbe8a61d3dffbc31b6b0a1851921d241f':
        raise ValueError('Original compiled SA image changed')
    runtime=json.loads((parent/'runtime-failure.json').read_text())
    if runtime['host_ready']!='X':raise ValueError('Original unknown handshake did not reproduce')
    modules_path=native/'registered_native/all-native.json'
    modules=json.loads(modules_path.read_text())['modules']
    state=json.loads((parent/'configuration-state.json').read_text())
    image=BitFile.load(parent/'quiesced.wbit')
    if audit(modules,state,image.words)['compared_configuration_bits']!=8736:
        raise ValueError('Incomplete original native frame agreement')
    spec_path=capsule/'model/resource/macro/fabulous/bitStreamSpec.bin'
    spec=PlainSpec(io.BytesIO(spec_path.read_bytes())).load()
    fasm=case/'design.fasm';features=fasm_features(fasm)
    pips=capsule/'model/resource/macro/fabulous/.FABulous/pips.txt'
    enabled=carry_modes(spec,modules,state)
    changes=[prove_input(t,l,i,spec,modules['LUT4x8_ha'],state,features,image.words,pips.read_text(),enabled)
             for t,l,i in TARGETS]
    if [c['observed_init'] for c in changes]!=[0xFFFF,0,0]:raise ValueError('Measured constant functions changed')
    if len({(c['word'],c['word_bit']) for c in changes})!=3:raise ValueError('Aliased repair selectors')
    out.mkdir(parents=True,exist_ok=False)
    export=json.loads((capsule/'leaf-audit.json').read_text())
    for row in export['native_exports'].values():
        path=capsule/row['path'].split('/build/r1_timing/',1)[1]
        if not path.resolve().is_relative_to(capsule) or sha(path)!=row['sha256']:raise ValueError('Native export changed')
        row['path']=str(path)
    (out/'native-audit.json').write_text(json.dumps(export,indent=2)+'\n');complete_native_exports(out/'native-audit.json')
    variants={}
    for mask in range(8):
        name=format(mask,'03b');folder=out/(name+'-case');folder.mkdir()
        words=list(image.words);expected=copy.deepcopy(state);selected=[c for i,c in enumerate(changes) if mask>>i&1]
        for c in selected:
            words[c['word']]|=1<<c['word_bit'];expected['tiles'][c['tile']]['q'][c['cell']]='1'
        if sum((a^b).bit_count() for a,b in zip(words,image.words))!=len(selected):raise ValueError('Unexpected image delta')
        if audit(modules,expected,words)['compared_configuration_bits']!=8736:raise ValueError('Expected frame audit incomplete')
        BitFile(0xFE,words).save(folder/'repair.wbit')
        report=dict(params=json.loads((case/'report.json').read_text())['params'],provenance=dict(
            bitfile_sha256=sha(folder/'repair.wbit'),kind='Derived existing-selector image, not fresh compiler output',
            parent_image_sha256=sha(parent/'quiesced.wbit'),changes=selected))
        (folder/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        variants[name]=dict(image_sha256=sha(folder/'repair.wbit'),changes=selected)
    bound=[Path(__file__).resolve(),functional/'result.json',parent/'runtime-failure.json',parent/'configuration-state.json',
           parent/'quiesced.wbit',spec_path,fasm,pips,modules_path,out/'native-audit.json']
    (out/'plan.json').write_text(json.dumps(dict(capsule=str(capsule),native=str(modules_path),variants=variants,
        inputs={str(p):sha(p) for p in bound},scope='Cofactor/carry-proved selector repair only; failed SA control preserved. Expected states are not native observations.'),indent=2)+'\n')


def run(out,pdk,icarus):
    if os.environ.get('GITHUB_ACTIONS')!='true':raise ValueError('Native repair campaign runs hosted')
    out,pdk,icarus=(Path(p).resolve() for p in (out,pdk,icarus));plan=json.loads((out/'plan.json').read_text())
    if any(sha(p)!=v for p,v in plan['inputs'].items()):raise ValueError('Repair source evidence changed')
    cap=Path(plan['capsule']);modules=json.loads(Path(plan['native']).read_text())['modules']
    os.environ['R1_RUNTIME_MODEL']=plan['native']
    result=dict(run=os.environ.get('GITHUB_RUN_ID'),source_sha=os.environ.get('GITHUB_SHA'),cases={},
        diagnostic_complete=False,repair_functional_passed=False,timing_acceptance=False,physical_acceptance=False,adopted=False)
    try:
        for name,row in plan['variants'].items():
            image=out/(name+'-case')/'repair.wbit'
            if sha(image)!=row['image_sha256']:raise ValueError('Derived image changed')
            error=None
            try:smoke(cap/'model/resource',image.parent,out/name,pdk=pdk,icarus_root=icarus,
                mapped_bundle=cap/'mapped/input',postphysical_complete=out/'native-audit.json',
                capture_configuration=True,restart_probe=True)
            except Exception as exc:error=str(exc)
            state=json.loads((out/name/'configuration-state.json').read_text())
            frame=audit(modules,state,BitFile.load(image).words)
            if frame['compared_configuration_bits']!=8736:raise ValueError('Actual repair frame audit incomplete')
            (out/name/'frame-audit.json').write_text(json.dumps(frame,indent=2)+'\n')
            result['cases'][name]=dict(passed=error is None,error=error,configuration_bits=8736,image_sha256=sha(image))
            if name=='000':
                failure=out/name/'runtime-failure.json'
                if not error or not failure.is_file() or json.loads(failure.read_text())['host_ready']!='X':
                    raise ValueError('Original native unknown control did not reproduce')
                result['control_reproduced']=True
            (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        passing=[n for n,r in result['cases'].items() if n!='000' and r['passed']]
        if passing:
            best=min(passing,key=lambda n:(len(plan['variants'][n]['changes']),n))
            image=out/(best+'-case')/'repair.wbit'
            smoke(cap/'model/resource',image.parent,out/'shell',pdk=pdk,icarus_root=icarus,
                mapped_bundle=cap/'mapped/input',postphysical_complete=out/'native-audit.json',
                capture_configuration=True,management_shell=True)
            direct=json.loads((out/best/'configuration-state.json').read_text())
            shell=json.loads((out/'shell/configuration-state.json').read_text())
            if direct!=shell:raise ValueError('Repair direct and reload observations differ')
            if audit(modules,shell,BitFile.load(image).words)['compared_configuration_bits']!=8736:
                raise ValueError('Repair reload frame audit incomplete')
            result.update(repair_functional_passed=True,selected_analysis_case=best)
        result['diagnostic_complete']=True
    except Exception as exc:
        result['error']=str(exc);raise
    finally:(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('prepare')
    for name in ('capsule','native','functional','out'):p.add_argument('--'+name,type=Path,required=True)
    p=sub.add_parser('run')
    for name in ('out','pdk','icarus'):p.add_argument('--'+name,type=Path,required=True)
    args=vars(parser.parse_args());mode=args.pop('mode');(prepare if mode=='prepare' else run)(**args)

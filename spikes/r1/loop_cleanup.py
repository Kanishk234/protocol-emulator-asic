"""Remove the remaining observed selected LUT loop with one existing bit."""
import argparse
import copy
import io
import json
from pathlib import Path

from assembly_catalog import sha
from compile.bitfile import BitFile
from compile.bitgen import fasm_features
from configuration_audit import audit
from profiling.r1_quiesce import PlainSpec,derive
from unused_input_sweep import prove_input,carry_modes,latch
from unused_feedback_repair import prepare as prepare_first
from sa_functional import run


def prepare(capsule,native,trial,functional,diagnostic,loaded,timing,out):
    capsule,native,trial,functional,diagnostic,loaded,timing,out=(Path(p).resolve() for p in
        (capsule,native,trial,functional,diagnostic,loaded,timing,out))
    data=json.loads((loaded/'result.json').read_text());measured=json.loads((timing/'result.json').read_text())
    if (str(data['run'])!='44786871916' or not data['passed'] or
            data['cases']['candidate']!=data['cases']['shell'] or
            str(measured['run'])!='44790210039' or not measured['diagnostic_complete'] or
            measured['model_qualified'] or measured['actual_native_run']!=data['run'] or
            any(r['structural_loops']!=1 for r in measured['models'].values()) or
            any(not r['passed'] for r in measured['coverage'].values())):
        raise ValueError('Require actual native success and complete loop-rejected timing')
    parent=loaded/'candidate';image=BitFile.load(parent/'quiesced.wbit')
    if sha(parent/'quiesced.wbit')!='cbf4300d88050502da6fcf167fcbbcbcd045ebd8b6aa7c36f92e05483c4aeb94':
        raise ValueError('Loaded first repair changed')
    state=json.loads((parent/'configuration-state.json').read_text())
    modules_path=native/'registered_native/all-native.json';modules=json.loads(modules_path.read_text())['modules']
    frame=audit(modules,state,image.words)
    if not frame['passed'] or frame['compared_configuration_bits']!=8736:raise ValueError('Parent frame audit fails')
    spec_path=capsule/'model/resource/macro/fabulous/bitStreamSpec.bin'
    spec=PlainSpec(io.BytesIO(spec_path.read_bytes())).load();pips=capsule/'model/resource/macro/fabulous/.FABulous/pips.txt'
    change=prove_input('X6Y3','E',0,spec,modules['LUT4x8_ha'],state,
        fasm_features(loaded/'candidate-case/design.fasm'),image.words,pips.read_text(),carry_modes(spec,modules,state))
    if (change['observed_init']!=0x330f or change['route_before'][-1]!=('X6Y3','LE_O') or
            change['route_after'][-1]!=('X2Y3','LF_O')):raise ValueError('Observed loop or alternative changed')
    source=latch(modules['LUT4x8_ha'],next(iter(spec['TileSpecs']['X2Y3']['F.FF'])))[0]
    if state['tiles']['Tile_X2Y3_LUT4x8_ha']['q'][source]!='1':
        raise ValueError('Alternative source is not an actual registered output')
    prepare_first(capsule,native,trial,functional,diagnostic,out)
    case=out/'candidate-case'
    if sha(case/'concurrency.wbit')!=sha(loaded/'candidate-case/concurrency.wbit'):
        raise ValueError('Reconstructed first repair differs from actual native parent')
    raw=BitFile.load(case/'concurrency.wbit');words=list(raw.words)
    if words[change['word']]>>change['word_bit']&1:raise ValueError('Raw selector not zero')
    words[change['word']]|=1<<change['word_bit'];BitFile(raw.arch_version,words).save(case/'concurrency.wbit')
    feature='X6Y3.J_l_EF_END0.LE_I0'
    if spec['TileSpecs']['X6Y3'][feature.split('.',1)[1]]!={change['tile_bit']:'1'}:
        raise ValueError('Alternative selector encoding changed')
    (case/'design.fasm').write_text((case/'design.fasm').read_text().rstrip()+'\n'+feature+'\n')
    report=json.loads((case/'report.json').read_text());report['provenance']['bitfile_sha256']=sha(case/'concurrency.wbit')
    report['provenance']['kind']='Derived two proved unused selectors from fixed placement image'
    report['provenance']['changes'].append(change)
    (case/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    expected_dir=out/'loop-expected';expected_dir.mkdir()
    derived,_,_=derive(capsule/'model/resource',case,case/'concurrency.wbit',expected_dir)
    expected_words=list(image.words);expected_words[change['word']]|=1<<change['word_bit']
    if BitFile.load(derived).words!=expected_words:raise ValueError('Additional quiescence changes')
    expected=copy.deepcopy(state);expected['tiles'][change['tile']]['q'][change['cell']]='1'
    frame=audit(modules,expected,expected_words)
    if not frame['passed'] or frame['compared_configuration_bits']!=8736:raise ValueError('Expected frame audit fails')
    (out/'loop-proof.json').write_text(json.dumps(dict(change=change,expected_frame_audit=frame,
        registered_alternative_source_latch=source,parent_native_run=data['run'],parent_timing_run=measured['run'],
        raw_image_sha256=sha(case/'concurrency.wbit'),expected_loaded_image_sha256=sha(derived),
        expected_states_are_not_observations=True),indent=2)+'\n')
    plan=json.loads((out/'plan.json').read_text());bound=[Path(p) for p in plan['input_sha256']]
    bound += [Path(__file__).resolve(),loaded/'result.json',parent/'configuration-state.json',parent/'quiesced.wbit',
              loaded/'candidate-case/design.fasm',timing/'result.json',out/'loop-proof.json',derived]
    plan['input_sha256']={str(p):sha(p) for p in bound};plan['repair']='D156 plus X6Y3/E.I0 unused feedback to existing registered source'
    (out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('prepare')
    for name in ('capsule','native','trial','functional','diagnostic','loaded','timing','out'):p.add_argument('--'+name,type=Path,required=True)
    p=sub.add_parser('run')
    for name in ('out','pdk','icarus'):p.add_argument('--'+name,type=Path,required=True)
    args=vars(parser.parse_args());mode=args.pop('mode');(prepare if mode=='prepare' else run)(**args)

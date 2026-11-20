"""Break one proved irrelevant selected feedback path in the stalled image."""
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
from sa_functional import prepare as prepare_native,run
from unused_input_sweep import prove_input,carry_modes


def prepare(capsule,native,trial,functional,diagnostic,out):
    capsule,native,trial,functional,diagnostic,out=(Path(p).resolve() for p in
        (capsule,native,trial,functional,diagnostic,out))
    data=json.loads((functional/'result.json').read_text())
    trace=(diagnostic/'delta.log').read_text()
    observer=json.loads((diagnostic/'delta-result.json').read_text())
    if (str(data['run'])!='44678070512' or data['passed'] or
            not all(data['cases'][s]['passed'] for s in ('control','reroute')) or
            str(observer['run'])!='44785764117' or
            not observer['cases']['control']['instrumented_test_passed'] or
            'DELTA_WATCHDOG stuck at tick 116000000' not in trace or
            'r1_tb.fabric.Tile_X3Y3_LUT4x8_ha._1322_.A1' not in trace):
        raise ValueError('Require preserved native failure and matching observer evidence')
    image=BitFile.load(functional/'candidate/quiesced.wbit')
    state=json.loads((functional/'candidate/configuration-state.json').read_text())
    modules_path=native/'registered_native/all-native.json'
    modules=json.loads(modules_path.read_text())['modules']
    if sha(modules_path)!='64922d92969e229e8562d9cc0c4bd1cb5add15766ec10709576f0255ebf2ce06':
        raise ValueError('Native frame source changed')
    frame=audit(modules,state,image.words)
    if not frame['passed'] or frame['compared_configuration_bits']!=8736:
        raise ValueError('Original actual frame disagreement')
    spec_path=capsule/'model/resource/macro/fabulous/bitStreamSpec.bin'
    spec=PlainSpec(io.BytesIO(spec_path.read_bytes())).load()
    pips=capsule/'model/resource/macro/fabulous/.FABulous/pips.txt'
    fasm=functional/'candidate-case/design.fasm'
    change=prove_input('X3Y3','D',0,spec,modules['LUT4x8_ha'],state,
        fasm_features(fasm),image.words,pips.read_text(),carry_modes(spec,modules,state))
    if (change['observed_init']!=0x0fcc or change['route_before'][-1]!=('X3Y3','LD_O') or
            ('X3Y3','LD_O') in change['route_after']):
        raise ValueError('Measured unused-input self feedback changed')
    prepare_native(capsule,native,trial,out,trial_kind='fixed_relocation')
    case=out/'candidate-case';raw=BitFile.load(case/'concurrency.wbit')
    if sha(case/'concurrency.wbit')!=sha(functional/'candidate-case/concurrency.wbit'):
        raise ValueError('Original candidate identity differs')
    words=list(raw.words)
    if words[change['word']]>>change['word_bit']&1:raise ValueError('Raw selector not zero')
    words[change['word']]|=1<<change['word_bit']
    BitFile(raw.arch_version,words).save(case/'concurrency.wbit')
    feature='X3Y3.J_l_CD_END0.LD_I0'
    if spec['TileSpecs']['X3Y3'][feature.split('.',1)[1]]!={change['tile_bit']:'1'}:
        raise ValueError('Alternate feature encoding changed')
    (case/'design.fasm').write_text(fasm.read_text().rstrip()+'\n'+feature+'\n')
    report=json.loads((case/'report.json').read_text())
    report['provenance']=dict(bitfile_sha256=sha(case/'concurrency.wbit'),
        kind='Derived one existing selector from fixed placement image; not fresh compiler output',
        parent_raw_image_sha256=sha(functional/'candidate-case/concurrency.wbit'),changes=[change])
    (case/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    expected_dir=out/'expected';expected_dir.mkdir()
    derived,_,_=derive(capsule/'model/resource',case,case/'concurrency.wbit',expected_dir)
    expected_words=list(image.words);expected_words[change['word']]|=1<<change['word_bit']
    if BitFile.load(derived).words!=expected_words:
        raise ValueError('Quiescence changes more than the single intended selector')
    expected=copy.deepcopy(state);expected['tiles'][change['tile']]['q'][change['cell']]='1'
    frame=audit(modules,expected,expected_words)
    if not frame['passed'] or frame['compared_configuration_bits']!=8736:
        raise ValueError('Expected derived frame mapping incomplete')
    (out/'repair-proof.json').write_text(json.dumps(dict(change=change,expected_frame_audit=frame,
        parent_native_run=data['run'],observer_run=observer['run'],raw_image_sha256=sha(case/'concurrency.wbit'),
        expected_loaded_image_sha256=sha(derived),expected_states_are_not_observations=True),indent=2)+'\n')
    plan=json.loads((out/'plan.json').read_text())
    bound=[Path(p) for p in plan['input_sha256']]
    bound += [Path(__file__).resolve(),functional/'result.json',functional/'candidate/quiesced.wbit',
              functional/'candidate/configuration-state.json',fasm,diagnostic/'delta.log',
              diagnostic/'delta-result.json',out/'repair-proof.json',derived,spec_path,pips]
    plan['input_sha256']={str(p):sha(p) for p in bound}
    plan['repair']='X3Y3/D.I0 cofactor-proved unused feedback selector only'
    (out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('prepare')
    for name in ('capsule','native','trial','functional','diagnostic','out'):p.add_argument('--'+name,type=Path,required=True)
    p=sub.add_parser('run')
    for name in ('out','pdk','icarus'):p.add_argument('--'+name,type=Path,required=True)
    args=vars(parser.parse_args());mode=args.pop('mode');(prepare if mode=='prepare' else run)(**args)

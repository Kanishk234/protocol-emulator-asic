"""Break a proved unused input feedback on the native SPI image's GND LUT."""
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
from unused_input_sweep import prove_input,carry_modes,latch


def prepare(capsule,native,trial,current,out):
    capsule,native,trial,current,out=(Path(p).resolve() for p in (capsule,native,trial,current,out))
    parent=current/'sa_functional';data=json.loads((parent/'result.json').read_text())
    log=current/'r1_loop_timing/routed_setup_static.log';text=log.read_text()
    if (str(data['run'])!='44799827748' or not data['passed'] or
            data['cases']['candidate']!=data['cases']['shell'] or
            not text.endswith('RUNSTA_END\n') or
            'Warning: There are 4 combinational loops in the design.' not in text or
            'Tile_X4Y1_LUT4x8_ha/_1056_/Y' not in text):
        raise ValueError('Require retained native pass and failed four-loop timing execution')
    old=parent/'candidate';image=BitFile.load(old/'quiesced.wbit')
    if sha(old/'quiesced.wbit')!='5af46fa505caf0702ea91cb68cf0ede6ad51e80b6f2cabe7ec54752cabe08031':
        raise ValueError('Actual native parent image changed')
    state=json.loads((old/'configuration-state.json').read_text())
    modules=json.loads((native/'registered_native/all-native.json').read_text())['modules']
    frame=audit(modules,state,image.words)
    if not frame['passed'] or frame['compared_configuration_bits']!=8736:raise ValueError('Parent frame disagreement')
    spec_path=capsule/'model/resource/macro/fabulous/bitStreamSpec.bin';spec=PlainSpec(io.BytesIO(spec_path.read_bytes())).load()
    pips=capsule/'model/resource/macro/fabulous/.FABulous/pips.txt';features=fasm_features(parent/'candidate-case/design.fasm')
    mod=modules['LUT4x8_ha'];entries=spec['TileSpecs']['X4Y1'];q=state['tiles']['Tile_X4Y1_LUT4x8_ha']['q']
    change=prove_input('X4Y1','G',0,spec,mod,state,features,image.words,pips.read_text(),carry_modes(spec,modules,state))
    if (change['observed_init']!=0 or change['route_before'][-1]!=('X4Y3','LC_O') or
            change['route_after'][-1]!=('X4Y1','LE_O') or
            q[latch(mod,next(iter(entries['G.I0mux'])))[0]]!='0'):
        raise ValueError('Measured constant-LUT feedback changed')
    source_name,source=latch(mod,next(iter(entries['E.FF'])))
    gate=mod['cells']['_0998_']
    drivers=[name for name,c in mod['cells'].items() if c['type']=='sg13cmos5l_dfrbpq_1' and c['connections']['Q']==gate['connections']['A1']]
    if (q[source_name]!='1' or gate['type']!='sg13cmos5l_mux2_1' or
            gate['connections']['S']!=source['connections']['Q'] or gate['connections']['X']!=mod['netnames']['LE_O']['bits'] or len(drivers)!=1):
        raise ValueError('Alternate source is not the actual selected native register')
    prepare_native(capsule,native,trial,out,trial_kind='spi_timer_free_run')
    case=out/'candidate-case'
    if sha(case/'concurrency.wbit')!=sha(parent/'candidate-case/concurrency.wbit'):
        raise ValueError('Compiled parent identity differs')
    raw=BitFile.load(case/'concurrency.wbit');words=list(raw.words)
    if words[change['word']]>>change['word_bit']&1:raise ValueError('Raw selector not zero')
    words[change['word']]|=1<<change['word_bit'];BitFile(raw.arch_version,words).save(case/'concurrency.wbit')
    feature='X4Y1.J_l_GH_END0.LG_I0'
    if entries[feature.split('.',1)[1]]!={change['tile_bit']:'1'}:raise ValueError('Selector encoding changed')
    (case/'design.fasm').write_text((case/'design.fasm').read_text().rstrip()+'\n'+feature+'\n')
    report=json.loads((case/'report.json').read_text());report['provenance']=dict(bitfile_sha256=sha(case/'concurrency.wbit'),
        kind='Derived one cofactor-proved constant-LUT unused selector from proven SPI compile',parent_raw_image_sha256=sha(parent/'candidate-case/concurrency.wbit'),changes=[change])
    (case/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    expected_dir=out/'expected-rail-repair';expected_dir.mkdir()
    derived,_,_=derive(capsule/'model/resource',case,case/'concurrency.wbit',expected_dir)
    expected_words=list(image.words);expected_words[change['word']]|=1<<change['word_bit']
    if BitFile.load(derived).words!=expected_words:raise ValueError('Quiescence changes more than the single selector')
    expected=copy.deepcopy(state);expected['tiles'][change['tile']]['q'][change['cell']]='1'
    frame=audit(modules,expected,expected_words)
    if not frame['passed'] or frame['compared_configuration_bits']!=8736:raise ValueError('Expected frame audit incomplete')
    (out/'rail-proof.json').write_text(json.dumps(dict(change=change,registered_source=drivers[0],source_selector=source_name,
        expected_frame_audit=frame,parent_run=data['run'],raw_image_sha256=sha(case/'concurrency.wbit'),
        expected_loaded_image_sha256=sha(derived),expected_states_are_not_observations=True),indent=2)+'\n')
    plan=json.loads((out/'plan.json').read_text());bound=[Path(p) for p in plan['input_sha256']]
    bound += [Path(__file__).resolve(),parent/'result.json',old/'quiesced.wbit',old/'configuration-state.json',log,
              spec_path,pips,out/'rail-proof.json',derived]
    plan['input_sha256']={str(p):sha(p) for p in bound};plan['repair']='Only X4Y1/G.I0: constant-zero LUT input from existing registered E source'
    (out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    x=sub.add_parser('prepare')
    for name in ('capsule','native','trial','current','out'):x.add_argument('--'+name,type=Path,required=True)
    x=sub.add_parser('run')
    for name in ('out','pdk','icarus'):x.add_argument('--'+name,type=Path,required=True)
    a=vars(p.parse_args());mode=a.pop('mode');(prepare if mode=='prepare' else run)(**a)

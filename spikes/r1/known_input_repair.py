"""Stage two fresh unused-input proofs after observing the exact raw native stall.

The timed-out raw run is diagnostic evidence only. The staged image still
requires every original native/reset/reload and connected timing check.
"""
import argparse
import io
import json
from pathlib import Path

from assembly_catalog import sha
from autonomy.check_xml import check_xml
from compile.bitfile import BitFile
from compile.bitgen import fasm_features,words as encode_words
from configuration_audit import audit
from profiling.r1_quiesce import PlainSpec,ground_unused
from sa_functional import prepare as prepare_native
from unused_input_sweep import prove_input,carry_modes

RAW='3fd72f5299e42d6bae148aab2d6d912a009f73e5426ded0f13482d7f9e061d66'
REPAIRED='5901ac357a973d4a5a72da105fd81f869be22ad0b5a5c475844cc90ddba691e7'


def validate_trace(trace,runtime):
    counts=dict(trace['signals'])
    expected={'Tile_X1Y1_LUT4x8_ha/LF_O','Tile_X1Y1_LUT4x8_ha/LC_O'}
    if (trace['time_ns']!=115921 or trace['events_at_same_time']!=4096 or
            sum(counts.values())!=4096 or len(counts)!=len(trace['signals']) or
            {n for n,v in counts.items() if v>1}!=expected or
            any(counts[n]<1000 for n in expected) or
            runtime['time_ns']!=115921 or runtime['pins']['h_wvalid']!='1' or
            runtime['pins']['h_wready']!='1'):
        raise ValueError('Require the exact raw native traffic-start delta observation')


def prepare(capsule,native,trial,baseline,out):
    capsule,native,trial,baseline,out=map(lambda p:Path(p).resolve(),(capsule,native,trial,baseline,out))
    plan=json.loads((baseline/'plan.json').read_text())
    if plan['trial_kind']!='spi_tick_known_inputs' or any(sha(p)!=h for p,h in plan['input_sha256'].items()):
        raise ValueError('Raw native source plan differs')
    if sha(baseline/'candidate-case/concurrency.wbit')!=RAW or (baseline/'candidate/configured-smoke.json').exists():
        raise ValueError('Require the rejected exact raw image, not a successful substitute')
    trace=baseline/'candidate/delta-trace/activity.json';runtime=baseline/'candidate/delta-trace/runtime.json'
    observed=json.loads(runtime.read_text());validate_trace(json.loads(trace.read_text()),observed)
    check_xml(baseline/'control/results.xml',1)
    control=json.loads((baseline/'control/configured-smoke.json').read_text())
    if not control['passed'] or not control['user_restart_probe_tested']:
        raise ValueError('Original native control did not pass')
    for p,h in control['input_sha256'].items():
        if sha(p)!=h:raise ValueError('Original native control input changed')
    modules=json.loads((native/'registered_native/all-native.json').read_text())['modules']
    state_path=baseline/'candidate/configuration-state.json';state=json.loads(state_path.read_text())
    loaded=BitFile.load(baseline/'candidate/quiesced.wbit')
    frame=audit(modules,state,loaded.words)
    if frame['compared_configuration_bits']!=8736:raise ValueError('Raw loaded frame census differs')
    prepare_native(capsule,native,trial,out,trial_kind='spi_tick_known_inputs')
    model=capsule/'model/resource';spec_path=model/'macro/fabulous/bitStreamSpec.bin'
    spec=PlainSpec(io.BytesIO(spec_path.read_bytes())).load()
    pips_path=model/'macro/fabulous/.FABulous/pips.txt';pips=pips_path.read_text()
    features=fasm_features(out/'candidate-case/design.fasm');carry=carry_modes(spec,modules,state)
    proofs=[];raw=BitFile.load(out/'candidate-case/concurrency.wbit');changed=list(raw.words)
    switches={kind:(model/'rtl'/(kind+'_switch_matrix.v')).read_text()
              for kind in set(spec['TileMap'].values())-{'NULL'}}
    expected,_=ground_unused(raw.words,spec,features,switches)
    if loaded.words!=expected:raise ValueError('Observed raw image differs from exact default grounding')
    for lut,init,address,terminal in [('C',0,(161,14),('X1Y2','LB_O')),('F',65535,(155,0),('X1Y3','LA_O'))]:
        proof=prove_input('X1Y1',lut,0,spec,modules['LUT4x8_ha'],state,features,loaded.words,pips,carry,allow_registered=True)
        if (proof['observed_init']!=init or proof['observed_ff_select']!='0' or
                (proof['word'],proof['word_bit'])!=address or tuple(proof['route_after'][-1])!=terminal or
                observed['tiles']['Tile_'+terminal[0]+'_LUT4x8_ha']['signals'][terminal[1]] not in ('0','1')):
            raise ValueError('Two-selector proof or observed source differs')
        mapping=[k for k,v in spec['TileSpecs']['X1Y1'].items()
                 if k.endswith('.L'+lut+'_I0') and v=={proof['tile_bit']:'1'}]
        if len(mapping)!=1:raise ValueError('Ambiguous repaired input FASM')
        features.append('X1Y1.'+mapping[0]);changed[proof['word']]|=1<<proof['word_bit'];proofs.append(proof)
    if sum((a^b).bit_count() for a,b in zip(raw.words,changed))!=2 or encode_words(features,spec)!=changed:
        raise ValueError('Repair changes more than the proved two selectors')
    image=out/'candidate-case/concurrency.wbit';BitFile(raw.arch_version,changed).save(image)
    if sha(image)!=REPAIRED:raise ValueError('Repaired image differs from the local diagnostic')
    (out/'candidate-case/design.fasm').write_text('\n'.join(features)+'\n')
    record=dict(raw_image_sha256=RAW,repaired_image_sha256=REPAIRED,changed_bits=2,
        actual_raw_frame_audit=frame,proofs=proofs,scope='Binary-unused routing repair only; fresh native/reload/timing required.',adopted=False)
    receipt=out/'two-selector-proof.json';receipt.write_text(json.dumps(record,indent=2)+'\n')
    staged=json.loads((out/'plan.json').read_text());staged['trial_kind']='spi_tick_known_inputs_two_selectors'
    bound=[Path(__file__),Path(__file__).with_name('unused_input_sweep.py'),
        Path(__file__).with_name('selected_route.py'),baseline/'plan.json',trace,runtime,state_path,
        baseline/'candidate/quiesced.wbit',baseline/'control/configured-smoke.json',baseline/'control/results.xml',
        spec_path,pips_path,receipt,out/'candidate-case/design.fasm',image,
        Path(__file__).parents[2]/'tools/profiling/r1_quiesce.py']
    staged['input_sha256'].update({str(p):sha(p) for p in bound})
    (out/'plan.json').write_text(json.dumps(staged,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('capsule','native','trial','baseline','out'):parser.add_argument('--'+name,type=Path,required=True)
    prepare(**vars(parser.parse_args()))

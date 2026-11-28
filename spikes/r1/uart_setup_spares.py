"""Park four proved-unused physical inputs on the qualified UART-buffer image.

Physical pin permutations are decoded from actual frames, never inferred from
logical nextpnr port names. This stages a new image; native/reload/RC must rerun.
"""
import argparse
import copy
import io
import json
from pathlib import Path
import shutil

from assembly_catalog import sha
from autonomy.check_xml import check_xml
from compile.bitfile import BitFile
from compile.bitgen import fasm_features,words as encode_words
from configuration_audit import audit
from global_support import flatten,TOP_SHA,NATIVE_SHA
from profiling.r1_quiesce import PlainSpec,ground_unused
from sa_functional import prepare as prepare_native
from unused_input_sweep import prove_input,carry_modes,carry_cone
from selected_route import selected_predecessors
from capture_spare_inputs import runtime_values,terminal_value

RAW='31ed78fda6153babc0bbdb11e8c2a1501cf4000b400bfbdd097fd095a8e5ed47'
LOADED='16675689e24f38145e8bd8f49cbde52501a831d643875b5d05db2ef0bcc2f770'
SNAPSHOT='aab3e40c2c6e9a57b78596b6dc8f5ab9de2be6da64fb1943817dc5b1ba096a3f'
CANDIDATE='1ad31736231b59f806f2b6bc1906351647af10aff1ec002cc9dd93027bcdc700'
TARGETS=(('X1Y1','H',0),('X4Y3','H',0),('X4Y3','H',3),('X5Y3','G',3))


def prepare(capsule,native,trial,source,out):
    capsule,native,trial,source,out=map(lambda p:Path(p).resolve(),(capsule,native,trial,source,out))
    parent=source/'sa_functional';data=json.loads((parent/'result.json').read_text())
    timing=json.loads((source/'r1_loop_timing/result.json').read_text())
    if (data['run']!='46175928642' or data['source_sha']!='6c34b82217aa58938ac9be8bbf4a70108a62620c'
            or data['passed'] is not True or data['cases']['candidate']!=data['cases']['shell']
            or timing['run']!=data['run'] or timing['source_sha']!=data['source_sha']
            or timing['model_qualified'] is not True or timing['models']['setup']['worst_slack_ns']!=-23.209684
            or timing['models']['hold']['worst_slack_ns']!=-1.56783
            or any(timing['models'][k]['structural_loops']!=0 or timing['models'][k]['loop_policy_sensitive']
                   for k in ('setup','hold'))
            or any(row['passed'] is not True for row in timing['coverage'].values())
            or data['cases']['candidate']!=dict(passed=True,image_sha256=LOADED,
                observed_configuration_sha256=SNAPSHOT,configuration_bits=8736)):
        raise ValueError('Require the exact native/reload/negative-RC qualified parent')
    for case in ('control','candidate','shell'):
        if data['cases'][case]['passed'] is not True or len(check_xml(parent/case/'results.xml',1))!=1:
            raise ValueError('Qualified native parent did not pass strict tests')
    if (sha(parent/'candidate-case/concurrency.wbit')!=RAW or
            sha(parent/'candidate/quiesced.wbit')!=LOADED or
            sha(parent/'candidate/configuration-state.json')!=SNAPSHOT):
        raise ValueError('Qualified parent image or observed state differs')
    prepare_native(capsule,native,trial,out,trial_kind='spi_tick_uart_buffer')
    for name in ('report.json','design.fasm','concurrency.wbit'):
        shutil.copyfile(parent/'candidate-case'/name,out/'candidate-case'/name)
    model=capsule/'model/resource';native_path=native/'registered_native/all-native.json';top_path=capsule/'analysis/top.json'
    if sha(native_path)!=NATIVE_SHA or sha(top_path)!=TOP_SHA:raise ValueError('Native or logical top changed')
    modules=json.loads(native_path.read_text())['modules'];top=json.loads(top_path.read_text())['modules']['eFPGA']
    state_path=parent/'candidate/configuration-state.json';state=json.loads(state_path.read_text())
    loaded=BitFile.load(parent/'candidate/quiesced.wbit');frame=audit(modules,state,loaded.words)
    if frame['compared_configuration_bits']!=8736:raise ValueError('Incomplete actual parent frame audit')
    runtime_path=parent/'candidate/runtime-after-load.json';runtime=json.loads(runtime_path.read_text())
    flat,_=flatten(top,modules,state['tiles']);values=runtime_values(flat,runtime)
    spec_path=model/'macro/fabulous/bitStreamSpec.bin';spec=PlainSpec(io.BytesIO(spec_path.read_bytes())).load()
    pips_path=model/'macro/fabulous/.FABulous/pips.txt';pips=pips_path.read_text()
    features=fasm_features(out/'candidate-case/design.fasm');carry=carry_modes(spec,modules,state)
    raw=BitFile.load(out/'candidate-case/concurrency.wbit');changed=list(raw.words);actual=list(loaded.words)
    switches={kind:(model/'rtl'/(kind+'_switch_matrix.v')).read_text() for kind in set(spec['TileMap'].values())-{'NULL'}}
    expected,_=ground_unused(raw.words,spec,features,switches)
    if expected!=loaded.words:raise ValueError('Parent differs from exact default grounding')
    proofs=[];addresses=set()
    for tile,lut,index in TARGETS:
        proof=prove_input(tile,lut,index,spec,modules['LUT4x8_ha'],state,features,loaded.words,pips,carry,allow_registered=True)
        if proof['observed_ff_select']!='0':raise ValueError('Setup-spare target is not combinational')
        proof['observed_terminal_value']=terminal_value(flat,values,state,*proof['route_after'][-1])
        address=(proof['word'],proof['word_bit'])
        if address in addresses or changed[address[0]]>>address[1]&1:raise ValueError('Overlapping or nonzero selector')
        addresses.add(address);changed[address[0]]|=1<<address[1];actual[address[0]]|=1<<address[1]
        target='L'+lut+'_I'+str(index)
        choices=[key for key,bits in spec['TileSpecs'][tile].items() if key.endswith('.'+target) and bits=={proof['tile_bit']:'1'}]
        if len(choices)!=1:raise ValueError('Ambiguous selector FASM')
        features.append(tile+'.'+choices[0]);proofs.append(proof)
    if sum((a^b).bit_count() for a,b in zip(raw.words,changed))!=4 or encode_words(features,spec)!=changed:
        raise ValueError('Full FASM does not match exactly four proved bits')
    graph=selected_predecessors(spec,actual,pips)
    for proof in proofs:
        if proof['input'] in (1,2):carry_cone(graph,proof['tile'].split('_')[1],proof['lut'],carry)
    image=out/'candidate-case/concurrency.wbit';BitFile(raw.arch_version,changed).save(image)
    if sha(image)!=CANDIDATE:raise ValueError('UART setup-spare image differs from fixed experiment')
    fasm=out/'candidate-case/design.fasm';fasm.write_text('\n'.join(features)+'\n')
    report_path=out/'candidate-case/report.json';original=out/'source-qualified-report.json';original.write_bytes(report_path.read_bytes())
    report=copy.deepcopy(json.loads(original.read_text()))
    if report['provenance']['bitfile_sha256']!=RAW:raise ValueError('Qualified report image differs')
    report.update(crc32=f'0x{BitFile.load(image).crc:08X}',words=len(changed),fmax_mhz=None,meets_50mhz=False,
        compiler_timing_applies_to_image=False,source_qualified_report_sha256=sha(original))
    report['provenance'].update(bitfile_sha256=CANDIDATE,derived_from_bitfile_sha256=RAW,
        scope='Qualified parent plus four cofactor/carry-proved physical spare-input selectors; no compiler timing claim.')
    report_path.write_text(json.dumps(report,indent=2)+'\n')
    receipt=out/'uart-setup-spare-proof.json';receipt.write_text(json.dumps(dict(parent_run=46175928642,
        source_raw_image_sha256=RAW,candidate_raw_image_sha256=CANDIDATE,changed_bits=4,
        actual_parent_frame_audit=frame,proofs=proofs,scope='Binary transition equality only; new native/reload/RC checks required.'),indent=2)+'\n')
    plan=json.loads((out/'plan.json').read_text());plan['trial_kind']='qualified_uart_setup_spares'
    bound=[Path(__file__),Path(__file__).with_name('capture_spare_inputs.py'),Path(__file__).with_name('unused_input_sweep.py'),Path(__file__).with_name('selected_route.py'),
        Path(__file__).with_name('global_support.py'),Path(__file__).with_name('uart_setup_spare_sources.json'),
        Path(__file__).parents[2]/'tools/profiling/r1_quiesce.py',top_path,native_path,state_path,runtime_path,
        parent/'candidate/quiesced.wbit',parent/'result.json',source/'r1_loop_timing/result.json',
        *[parent/case/'results.xml' for case in ('control','candidate','shell')],
        *[parent/'candidate-case'/n for n in ('report.json','design.fasm','concurrency.wbit')],
        spec_path,pips_path,receipt,original,report_path,fasm,image]
    plan['input_sha256'].update({str(p):sha(p) for p in bound})
    (out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('capsule','native','trial','source','out'):parser.add_argument('--'+name,type=Path,required=True)
    prepare(**vars(parser.parse_args()))

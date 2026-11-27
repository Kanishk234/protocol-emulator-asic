"""Park twelve proved-unused physical inputs on the qualified SPI capture image.

Physical pin permutations are decoded from actual frames, never inferred from
logical nextpnr port names. This stages a new image; native/reload/RC must rerun.
"""
import argparse
import copy
import io
import json
from pathlib import Path
import re
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

RAW='5901ac357a973d4a5a72da105fd81f869be22ad0b5a5c475844cc90ddba691e7'
LOADED='a4cbccd01be782a01a548e853f065076093de60221bdadda012874ed79206ec5'
SNAPSHOT='71c9c11bc0b8af802cdbfcf6baed78e5198b597f5f529ede618beacc048f9d36'
CANDIDATE='0d51924b9ad26a1993e41889be1bf0756dd40870041304dd7db8947c85191657'
TARGETS=(('X3Y1','A',0),('X3Y1','A',1),('X3Y1','A',2),
         ('X2Y1','B',0),('X2Y1','B',1),('X2Y1','B',2),
         ('X3Y1','C',0),('X2Y1','E',2),('X2Y1','C',1),
         ('X2Y1','C',2),('X2Y1','C',3),('X2Y3','D',1))


def runtime_values(flat,runtime):
    values={}
    for tile,row in runtime['tiles'].items():
        for name,cell in row['cells'].items():
            model=flat['cells'].get(tile+'/'+name)
            if model is None:
                if cell['type'] not in ('sg13cmos5l_tiehi','sg13cmos5l_tielo'):
                    raise ValueError('Runtime contains an unknown native cell')
                continue
            for pin,value in cell['pins'].items():
                if pin not in model['connections']:continue
                bits=model['connections'][pin]
                if len(bits)!=len(value):raise ValueError('Runtime pin width differs')
                for bit,v in zip(bits,reversed(value)):
                    if v not in '01XZ' or bit in values and values[bit]!=v:
                        raise ValueError('Conflicting or invalid runtime bit')
                    values[bit]=v
    return values


def terminal_value(flat,values,state,tile,signal):
    names=[name for name in state['tiles'] if name.split('_')[1]==tile]
    if len(names)!=1:raise ValueError('Ambiguous terminal tile')
    prefix=names[0]+'/';bits=None
    for key in (prefix+signal,prefix+signal+'_top'):
        if key in flat['netnames']:bits=flat['netnames'][key]['bits'];break
    if bits is None:
        match=re.fullmatch(r'(S[AB]_q)([0-7])',signal)
        if match and prefix+match[1] in flat['netnames']:
            bits=[flat['netnames'][prefix+match[1]]['bits'][int(match[2])]]
    if bits is None or len(bits)!=1 or values.get(bits[0]) not in ('0','1'):
        raise ValueError('Selected terminal is not observed-defined')
    return values[bits[0]]


def prepare(capsule,native,trial,source,out):
    capsule,native,trial,source,out=map(lambda p:Path(p).resolve(),(capsule,native,trial,source,out))
    parent=source/'sa_functional';data=json.loads((parent/'result.json').read_text())
    timing=json.loads((source/'r1_loop_timing/result.json').read_text())
    if (data['run']!='46045747168' or data['source_sha']!='32796d4a62dcef8d6bbf4fcdc0754a829bbbf275'
            or data['passed'] is not True or data['cases']['candidate']!=data['cases']['shell']
            or timing['run']!=data['run'] or timing['source_sha']!=data['source_sha']
            or timing['model_qualified'] is not True or timing['models']['setup']['worst_slack_ns']!=-34.141884
            or timing['models']['hold']['worst_slack_ns']!=-1.226009
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
    prepare_native(capsule,native,trial,out,trial_kind='spi_tick_known_inputs')
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
        if proof['observed_ff_select']!='1':raise ValueError('Capture target is not registered')
        proof['observed_terminal_value']=terminal_value(flat,values,state,*proof['route_after'][-1])
        address=(proof['word'],proof['word_bit'])
        if address in addresses or changed[address[0]]>>address[1]&1:raise ValueError('Overlapping or nonzero selector')
        addresses.add(address);changed[address[0]]|=1<<address[1];actual[address[0]]|=1<<address[1]
        target='L'+lut+'_I'+str(index)
        choices=[key for key,bits in spec['TileSpecs'][tile].items() if key.endswith('.'+target) and bits=={proof['tile_bit']:'1'}]
        if len(choices)!=1:raise ValueError('Ambiguous selector FASM')
        features.append(tile+'.'+choices[0]);proofs.append(proof)
    if sum((a^b).bit_count() for a,b in zip(raw.words,changed))!=12 or encode_words(features,spec)!=changed:
        raise ValueError('Full FASM does not match exactly twelve proved bits')
    graph=selected_predecessors(spec,actual,pips)
    for proof in proofs:
        if proof['input'] in (1,2):carry_cone(graph,proof['tile'].split('_')[1],proof['lut'],carry)
    image=out/'candidate-case/concurrency.wbit';BitFile(raw.arch_version,changed).save(image)
    if sha(image)!=CANDIDATE:raise ValueError('Capture-spare image differs from fixed experiment')
    fasm=out/'candidate-case/design.fasm';fasm.write_text('\n'.join(features)+'\n')
    report_path=out/'candidate-case/report.json';original=out/'source-qualified-report.json';original.write_bytes(report_path.read_bytes())
    report=copy.deepcopy(json.loads(original.read_text()))
    if report['provenance']['bitfile_sha256']!=RAW:raise ValueError('Qualified report image differs')
    report.update(crc32=f'0x{BitFile.load(image).crc:08X}',words=len(changed),fmax_mhz=None,meets_50mhz=False,
        compiler_timing_applies_to_image=False,source_qualified_report_sha256=sha(original))
    report['provenance'].update(bitfile_sha256=CANDIDATE,derived_from_bitfile_sha256=RAW,
        scope='Qualified parent plus twelve cofactor/carry-proved physical spare-input selectors; no compiler timing claim.')
    report_path.write_text(json.dumps(report,indent=2)+'\n')
    receipt=out/'capture-spare-proof.json';receipt.write_text(json.dumps(dict(parent_run=46045747168,
        source_raw_image_sha256=RAW,candidate_raw_image_sha256=CANDIDATE,changed_bits=12,
        actual_parent_frame_audit=frame,proofs=proofs,scope='Binary transition equality only; new native/reload/RC checks required.'),indent=2)+'\n')
    plan=json.loads((out/'plan.json').read_text());plan['trial_kind']='qualified_spi_capture_spares'
    bound=[Path(__file__),Path(__file__).with_name('unused_input_sweep.py'),Path(__file__).with_name('selected_route.py'),
        Path(__file__).with_name('global_support.py'),Path(__file__).with_name('capture_spare_sources.json'),
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

"""Redirect one proved unused input upstream selector to an existing register."""
import argparse
from collections import defaultdict
import copy
import io
import json
from pathlib import Path

from assembly_catalog import sha
from compile.bitfile import BitFile
from compile.bitgen import fasm_features
from configuration_audit import audit
from profiling.r1_quiesce import PlainSpec,derive
from selected_route import selected_predecessors,trace_route
from unused_input_sweep import prove_input,carry_modes,latch
from unused_lut_probe import registered_h_source
from loop_cleanup import prepare as prepare_parent
from sa_functional import run


def prepare(capsule,native,trial,functional,diagnostic,loaded,timing,current,out):
    capsule,native,trial,functional,diagnostic,loaded,timing,current,out=(Path(p).resolve() for p in
        (capsule,native,trial,functional,diagnostic,loaded,timing,current,out))
    parent=current/'sa_functional';data=json.loads((parent/'result.json').read_text())
    measured=json.loads((current/'r1_loop_timing/result.json').read_text())
    if (str(data['run'])!='44792141462' or not data['passed'] or
            data['cases']['candidate']!=data['cases']['shell'] or
            measured['run']!=data['run'] or not measured['model_qualified'] or
            measured['models']['setup']['worst_slack_ns']!=-10.193067 or
            any(r['structural_loops'] or r['loop_policy_sensitive'] for r in measured['models'].values())):
        raise ValueError('Require actual two-selector native pass and qualified failing timing')
    image=BitFile.load(parent/'candidate/quiesced.wbit')
    if sha(parent/'candidate/quiesced.wbit')!='39e2aadc8b7f25b5838bde7bcff746910105a07f9e3cce6d49c0d29cf711b739':
        raise ValueError('Actual parent image changed')
    state=json.loads((parent/'candidate/configuration-state.json').read_text())
    modules=json.loads((native/'registered_native/all-native.json').read_text())['modules']
    if not audit(modules,state,image.words)['passed']:raise ValueError('Actual parent frame disagreement')
    spec_path=capsule/'model/resource/macro/fabulous/bitStreamSpec.bin';spec=PlainSpec(io.BytesIO(spec_path.read_bytes())).load()
    pips=capsule/'model/resource/macro/fabulous/.FABulous/pips.txt';f=fasm_features(parent/'candidate-case/design.fasm')
    proof=prove_input('X2Y3','D',1,spec,modules['LUT4x8_ha'],state,f,image.words,pips.read_text(),carry_modes(spec,modules,state))
    if proof['observed_init']!=0xaa00:raise ValueError('Actual unused D input function changed')
    entries=spec['TileSpecs']['X2Y3'];feature='JE2END4.J2MID_CDa_BEG1';mapping=entries[feature]
    if mapping!={183:'1'}:raise ValueError('Existing upstream selector encoding changed')
    if any(x.startswith('X2Y3.') and set(entries[x.split('.',1)[1]])&set(mapping) for x in f):
        raise ValueError('Upstream selector overlaps an active feature')
    name,cell=latch(modules['LUT4x8_ha'],183)
    selector=modules['LUT4x8_ha']['netnames']['Inst_LUT4x8_ha_switch_matrix.inst_cus_mux21_J2MID_CDa_BEG1.S']['bits']
    if cell['connections']['Q']!=selector:raise ValueError('Native upstream selector latch identity changed')
    if state['tiles']['Tile_X2Y3_LUT4x8_ha']['q'][name]!='0':raise ValueError('Upstream selector not zero')
    graph=selected_predecessors(spec,image.words,pips.read_text());successors=defaultdict(set)
    for node,preds in graph.items():
        for predecessor in preds:successors[predecessor].add(node)
    seen=set();todo=[('X2Y3','J2MID_CDa_BEG1')];ends=set()
    while todo:
        node=todo.pop()
        if node in seen:continue
        seen.add(node)
        if not successors[node]:ends.add(node)
        todo.extend(successors[node])
    if len(seen)!=3 or ends!={('X2Y3','LD_I1')}:raise ValueError('Upstream selector has other selected consumers')
    h_name,h=latch(modules['LUT4x8_ha'],next(iter(entries['H.FF'])))
    if state['tiles']['Tile_X2Y3_LUT4x8_ha']['q'][h_name]!='1' or 'X2Y3.H.FF' not in f:
        raise ValueError('Alternative H source is not actually registered')
    source_register=registered_h_source(modules['LUT4x8_ha'],h['connections']['Q'][0])
    before=trace_route(graph,('X2Y3','LD_I1'));expected_words=list(image.words);expected_words[273]|=1<<23
    after=trace_route(selected_predecessors(spec,expected_words,pips.read_text()),('X2Y3','LD_I1'))
    if before[-1]!=('X3Y3','LF_O') or after[-1]!=('X2Y3','LH_O'):
        raise ValueError('Measured long-input to registered-source reroute changed')
    change=dict(tile='Tile_X2Y3_LUT4x8_ha',cell=name,tile_bit=183,word=273,word_bit=23,before='0',after='1',
        feature='X2Y3.'+feature,cofactor_proof=proof,selected_downstream_nodes=sorted(seen),
        registered_source=source_register,route_before=before,route_after=after)
    prepare_parent(capsule,native,trial,functional,diagnostic,loaded,timing,out)
    case=out/'candidate-case'
    if sha(case/'concurrency.wbit')!=sha(parent/'candidate-case/concurrency.wbit'):
        raise ValueError('Reconstructed actual parent differs')
    raw=BitFile.load(case/'concurrency.wbit');words=list(raw.words)
    if words[273]>>23&1:raise ValueError('Raw upstream selector not zero')
    words[273]|=1<<23;BitFile(raw.arch_version,words).save(case/'concurrency.wbit')
    (case/'design.fasm').write_text((case/'design.fasm').read_text().rstrip()+'\nX2Y3.'+feature+'\n')
    report=json.loads((case/'report.json').read_text());report['provenance']['bitfile_sha256']=sha(case/'concurrency.wbit')
    report['provenance']['kind']='Derived three proved unused selectors from fixed placement image'
    report['provenance']['changes'].append(change);(case/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    expected_dir=out/'upstream-expected';expected_dir.mkdir()
    derived,_,_=derive(capsule/'model/resource',case,case/'concurrency.wbit',expected_dir)
    if BitFile.load(derived).words!=expected_words:raise ValueError('Additional quiescence changes')
    expected=copy.deepcopy(state);expected['tiles'][change['tile']]['q'][name]='1'
    frame=audit(modules,expected,expected_words)
    if not frame['passed'] or frame['compared_configuration_bits']!=8736:raise ValueError('Expected frame disagreement')
    (out/'upstream-proof.json').write_text(json.dumps(dict(change=change,expected_frame_audit=frame,
        parent_run=data['run'],raw_image_sha256=sha(case/'concurrency.wbit'),expected_loaded_image_sha256=sha(derived),
        expected_states_are_not_observations=True),indent=2)+'\n')
    plan=json.loads((out/'plan.json').read_text());bound=[Path(p) for p in plan['input_sha256']]
    bound += [Path(__file__).resolve(),parent/'result.json',parent/'candidate/quiesced.wbit',
              parent/'candidate/configuration-state.json',current/'r1_loop_timing/result.json',out/'upstream-proof.json',derived]
    plan['input_sha256']={str(p):sha(p) for p in bound};plan['repair']='D157 plus only unused D.I1 upstream selector to existing registered H'
    (out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('prepare')
    for name in ('capsule','native','trial','functional','diagnostic','loaded','timing','current','out'):p.add_argument('--'+name,type=Path,required=True)
    p=sub.add_parser('run')
    for name in ('out','pdk','icarus'):p.add_argument('--'+name,type=Path,required=True)
    args=vars(parser.parse_args());mode=args.pop('mode');(prepare if mode=='prepare' else run)(**args)

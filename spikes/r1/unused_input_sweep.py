"""Bounded image-only timing experiment on proved unused primary LUT inputs.

Derived states are expected image states, never new native observations. No
candidate is adopted without actual loading and protocol/reset/reload tests.
"""
import argparse
from collections import defaultdict
import copy
import json
import os
from pathlib import Path
import subprocess

from assembly_catalog import sha
from routed_timing import annotation,assert_cases,observed_cases
from run_timing import compare,parse_log

TARGETS=(('X1Y2','F',2),('X1Y2','F',3),('X1Y3','D',3))


def independent(init,index):
    if type(init) is not int or not 0<=init<65536 or type(index) is not int or not 0<=index<4:
        raise ValueError('Invalid LUT truth table/input')
    return all(((init>>a)&1)==((init>>(a^(1<<index)))&1) for a in range(16))


def latch(module,index):
    frame,offset=divmod(index,32)
    matches=[(name,c) for name,c in module['cells'].items() if c['type']=='sg13cmos5l_dlhq_1'
        and c['connections'].get('D')==[module['ports']['FrameData']['bits'][offset]]
        and c['connections'].get('GATE')==[module['ports']['FrameStrobe']['bits'][frame]]]
    if len(matches)!=1:raise ValueError('Missing unique physical selector latch')
    return matches[0]


def carry_cone(graph,tile,lut,enabled):
    """I1/I2 also feed carry: reject every reachable enabled carry consumer."""
    successors=defaultdict(set)
    for dest,preds in graph.items():
        for source in preds:successors[source].add(dest)
    for node in enabled:
        successors[node].add((node[0],node[1].replace('_Ci','_Co')))
    visited=set();todo=[(tile,'L'+lut+'_Co')];consumers=[]
    while todo:
        node=todo.pop()
        if node in visited:continue
        visited.add(node);name=node[1]
        if not (name in ('CI0','CO0') or len(name)==5 and name[0]=='L' and name[1] in 'ABCDEFGH' and name[2:] in ('_Ci','_Co')):
            raise ValueError('Unexpected non-carry fanout of changed carry input')
        if name.endswith('_Ci'):
            if node not in enabled or enabled[node]:raise ValueError('Changed input can reach an enabled carry consumer')
            consumers.append(node)
        todo.extend(successors[node])
    return dict(visited_nodes=len(visited),disabled_carry_consumers=sorted(consumers),enabled_consumers=0)


def carry_modes(spec,modules,state):
    enabled={}
    for native,row in state['tiles'].items():
        if row['tile_type']!='LUT4x8_ha':continue
        xy=native.split('_')[1]
        for letter in 'ABCDEFGH':
            mapping=spec['TileSpecs'][xy][letter+'.I0mux']
            if len(mapping)!=1 or list(mapping.values())!=['1']:raise ValueError('Unexpected carry input mux encoding')
            name,_=latch(modules['LUT4x8_ha'],next(iter(mapping)));value=row['q'][name]
            if value not in ('0','1'):raise ValueError('Unknown actual carry input mode')
            enabled[(xy,'L'+letter+'_Ci')]=value=='1'
    if len(enabled)!=128:raise ValueError('Incomplete native carry-consumer census')
    return enabled


def ff_mode(tile,lut,spec,module,state,features,words,allow_registered=False):
    mapping=spec['TileSpecs'][tile][lut+'.FF']
    if len(mapping)!=1 or list(mapping.values())!=['1']:
        raise ValueError('Unexpected FF mode encoding')
    address=next(iter(mapping));name,_=latch(module,address)
    value=state['tiles']['Tile_'+tile+'_LUT4x8_ha']['q'][name]
    if value not in ('0','1'):raise ValueError('Unknown actual FF mode')
    if value=='1' and not allow_registered:raise ValueError('Require the measured combinational LUT')
    if allow_registered:
        x,y=map(int,tile[1:].split('Y'));frame,offset=divmod(address,32)
        word=1+(x*20+frame)*6+1+(4-y)
        if int(value)!=int(tile+'.'+lut+'.FF' in features) or (words[word]>>offset)&1!=int(value):
            raise ValueError('Observed FF mode differs from image/FASM')
    return value


def prove_lut_independent(tile,lut,index,spec,module,state,features,words,allow_registered=False):
    """Check the function/mode without proposing any routing-bit change."""
    native='Tile_'+tile+'_LUT4x8_ha';entries=spec['TileSpecs'][tile]
    init=0
    for bit in range(16):
        key=lut+'.INIT'+('' if bit==0 else '['+str(bit)+']');mapping=entries[key]
        if len(mapping)!=1 or list(mapping.values())!=['1']:raise ValueError('Unexpected LUT encoding')
        name,_=latch(module,next(iter(mapping)));value=state['tiles'][native]['q'][name]
        declared=tile+'.'+key in features or (bit==0 and tile+'.'+lut+'.INIT[0]' in features)
        if value not in ('0','1') or int(value)!=int(declared):raise ValueError('Observed truth differs from primary FASM')
        init|=int(value)<<bit
    if not independent(init,index):raise ValueError('LUT function depends on selected input')
    mode=ff_mode(tile,lut,spec,module,state,features,words,allow_registered)
    return init,mode


def prove_input(tile,lut,index,spec,module,state,features,words,pips,carry_enabled,allow_registered=False):
    from selected_route import selected_predecessors,trace_route
    native='Tile_'+tile+'_LUT4x8_ha';entries=spec['TileSpecs'][tile];target='L'+lut+'_I'+str(index)
    if any(f.split('.')[0]==tile and f.split('.')[2]==target for f in features):
        raise ValueError('Cannot change an actively routed LUT input')
    init,mode=prove_lut_independent(tile,lut,index,spec,module,state,features,words,allow_registered)
    alternatives=[(k,v) for k,v in entries.items() if k.endswith('.'+target)]
    if len(alternatives)!=2 or {tuple(v.values()) for k,v in alternatives}!={('0',),('1',)}:
        raise ValueError('Require one existing two-way input selector')
    address=next(iter(alternatives[0][1]))
    if any(set(v)!={address} for k,v in alternatives):raise ValueError('Selector encodings disagree')
    locked=set()
    for f in features:
        t,source,dest=f.split('.')
        if t==tile:locked.update(entries[source+'.'+dest])
    if address in locked:raise ValueError('Selector overlaps an active feature')
    if allow_registered and any(address in mapping for key,mapping in entries.items()
            if any(key.startswith(letter+'.') for letter in 'ABCDEFGH')):
        raise ValueError('Input selector overlaps primitive state/clock/control fields')
    name,cell=latch(module,address)
    selector=module['netnames']['Inst_LUT4x8_ha_switch_matrix.inst_cus_mux21_'+target+'.S']['bits']
    if cell['connections']['Q']!=selector or state['tiles'][native]['q'][name]!='0':
        raise ValueError('Actual native selector identity/state differs')
    x,y=map(int,tile[1:].split('Y'));frame,offset=divmod(address,32)
    word=1+(x*20+frame)*6+1+(4-y)
    if (words[word]>>offset)&1:raise ValueError('Parent image selector is not zero')
    candidate=list(words);candidate[word]|=1<<offset
    carry=(carry_cone(selected_predecessors(spec,words,pips),tile,lut,carry_enabled)
           if index in (1,2) else dict(scope='I0/I3 do not enter the native carry function'))
    proof=dict(tile=native,cell=name,lut=lut,input=index,observed_init=init,cofactor_addresses_checked=16,
                tile_bit=address,word=word,word_bit=offset,before='0',after='1',carry_noninterference=carry,
                route_before=trace_route(selected_predecessors(spec,words,pips),(tile,target)),
                route_after=trace_route(selected_predecessors(spec,candidate,pips),(tile,target)))
    if allow_registered:
        proof.update(observed_ff_select=mode,primitive_control_fields_preserved=True,
            transition_scope='Binary LUT data equality; unchanged FF/clock/reset/enable modes preserve sequential transitions. No native initialization, glitch or timing acceptance.')
    return proof


def prepare(rc,proof,native,capsule,pdk,out):
    import io
    from compile.bitfile import BitFile
    from compile.bitgen import fasm_features
    from configuration_audit import audit
    from profiling.r1_quiesce import PlainSpec
    from routed_timing import prepare as prepare_parent
    from unused_lut_probe import change_case
    rc,proof,native,capsule,pdk,out=(Path(p).resolve() for p in (rc,proof,native,capsule,pdk,out))
    out.mkdir(parents=True,exist_ok=False)
    prepare_parent(rc,proof,native,capsule,pdk,out/'baseline')
    parent=native/'registered_functional/candidate';image=BitFile.load(parent/'registered-input.wbit')
    state=json.loads((parent/'configuration-state.json').read_text())
    modules=json.loads((native/'registered_native/all-native.json').read_text())['modules']
    spec_path=capsule/'model/resource/macro/fabulous/bitStreamSpec.bin'
    pips_path=capsule/'model/resource/macro/fabulous/.FABulous/pips.txt'
    fasm=capsule/'model/compile/uart_spi_11/design.fasm'
    spec=PlainSpec(io.BytesIO(spec_path.read_bytes())).load();features=fasm_features(fasm)
    top=json.loads((capsule/'analysis/top.json').read_text())['modules']['eFPGA']
    if any('CI0' in p or 'CO0' in p for p in top['ports']):raise ValueError('Original carry has an external root observer')
    enabled=carry_modes(spec,modules,state)
    changes=[prove_input(t,l,i,spec,modules['LUT4x8_ha'],state,features,image.words,pips_path.read_text(),enabled) for t,l,i in TARGETS]
    variants={}
    for mask in range(1,8):
        name=format(mask,'03b');folder=out/name;folder.mkdir()
        words=list(image.words);expected=copy.deepcopy(state);selected=[c for i,c in enumerate(changes) if (mask>>i)&1]
        for c in selected:
            words[c['word']]|=1<<c['word_bit'];expected['tiles'][c['tile']]['q'][c['cell']]='1'
        if sum((a^b).bit_count() for a,b in zip(words,image.words))!=len(selected):
            raise ValueError('Image changes exceed the individually proved selectors')
        candidate=folder/'candidate.wbit';BitFile(image.arch_version,words).save(candidate)
        expected['scope']='Expected derived image states, not an actual loading observation.'
        (folder/'expected-state.json').write_text(json.dumps(expected)+'\n')
        a=audit(modules,expected,words)
        if not a['passed'] or a['compared_configuration_bits']!=8736:raise ValueError('Expected image/frame agreement fails')
        a['scope']='Decoded expected-state/image agreement only; no actual candidate loading observation.'
        (folder/'expected-frame-audit.json').write_text(json.dumps(a,indent=2)+'\n')
        scripts={}
        for kind in ('routed_setup','routed_hold'):
            for policy in ('static','dynamic'):
                label=kind+'_'+policy;text=(out/'baseline'/(label+'.tcl')).read_text()
                for c in selected:text=change_case(text,c)
                assert_cases(text,observed_cases(expected))
                script=folder/(label+'.tcl');script.write_text(text);scripts[label]=sha(script)
        variants[name]=dict(changes=selected,image_sha256=sha(candidate),expected_state_sha256=sha(folder/'expected-state.json'),scripts=scripts)
    paths=[Path(__file__),spec_path,pips_path,fasm,native/'registered_native/all-native.json',out/'baseline/plan.json']
    (out/'plan.json').write_text(json.dumps(dict(input_sha256={str(p):sha(p) for p in paths},changes=changes,variants=variants,
        scope='Analysis-only primary-image selector sensitivity, unchanged hardware/20ns/0.25ns constraints. Every change is truth-independent and absent from active FASM. Native loading/protocol/reset/reload validation still required.'),indent=2)+'\n')


def run(out):
    from routed_timing import run as run_parent
    out=Path(out).resolve();plan=json.loads((out/'plan.json').read_text())
    if any(sha(p)!=v for p,v in plan['input_sha256'].items()):raise ValueError('Frozen sensitivity inputs changed')
    try:run_parent(out/'baseline')
    except SystemExit:pass
    parent=json.loads((out/'baseline/result.json').read_text())
    if (not parent['diagnostic_complete'] or parent['error']!='Configured macro setup/hold or loop-policy check fails'
            or abs(parent['models']['routed_setup']['worst_slack_ns']+11.108903)>1e-6
            or abs(parent['models']['routed_hold']['worst_slack_ns']+1.870506)>1e-6):
        raise ValueError('Original connected timing control did not reproduce')
    results={'000':dict(models=parent['models'],qualified=True,actually_loaded_parent=True)}
    for name,row in plan['variants'].items():
        folder=out/name;result=dict(qualified=False,actually_loaded=False)
        try:
            if sha(folder/'candidate.wbit')!=row['image_sha256'] or sha(folder/'expected-state.json')!=row['expected_state_sha256']:
                raise ValueError('Candidate image or expected states changed')
            models={};coverage={}
            for kind in ('routed_setup','routed_hold'):
                logs=[]
                for policy in ('static','dynamic'):
                    label=kind+'_'+policy;script=folder/(label+'.tcl')
                    if sha(script)!=row['scripts'][label]:raise ValueError('Candidate case constraints changed')
                    with (folder/(label+'.log')).open('w') as stream:
                        proc=subprocess.run(['sta','-exit',str(script)],stdout=stream,stderr=subprocess.STDOUT,timeout=240)
                    if proc.returncode:raise ValueError('Native candidate STA failed')
                    text=(folder/(label+'.log')).read_text();logs.append(parse_log(text));coverage[label]=annotation(text)
                models[kind]=compare(*logs)
            result.update(models=models,coverage=coverage,qualified=all(a['passed'] for a in coverage.values()) and
                all(not m['loop_policy_sensitive'] and m['structural_loops']==0 for m in models.values()))
            result['necessary_constraints_met']=result['qualified'] and all(m['worst_slack_ns']>=0 for m in models.values())
        except Exception as exc:result['error']=str(exc)
        results[name]=result
    qualified={n:r for n,r in results.items() if r['qualified']}
    def margin(row):return min(row['models'][k]['worst_slack_ns'] for k in ('routed_setup','routed_hold'))
    best=max(qualified,key=lambda n:margin(qualified[n]))
    result=dict(diagnostic_complete=True,run=os.environ.get('GITHUB_RUN_ID'),source_sha=os.environ.get('GITHUB_SHA'),
        variants=results,best_analysis_case=best,improves_parent=margin(qualified[best])>margin(results['000']),
        physical_acceptance=False,timing_acceptance=False,requires_actual_native_loading=True,scope=plan['scope'])
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('prepare')
    for name in ('rc','proof','native','capsule','pdk','out'):p.add_argument('--'+name,type=Path,required=True)
    sub.add_parser('run').add_argument('--out',type=Path,required=True)
    args=vars(parser.parse_args());mode=args.pop('mode');(prepare if mode=='prepare' else run)(**args)

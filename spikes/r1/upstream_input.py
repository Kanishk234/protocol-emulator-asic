"""Prove a free upstream selector affects only one unused LUT input.

Binary noninterference only. Native initialization/reload and timing are
separate acceptance gates; this function neither writes nor accepts an image.
"""
from collections import defaultdict

from selected_route import selected_predecessors,trace_route
from unused_input_sweep import prove_lut_independent,latch,carry_cone


def isolated_chain(graph,start,target):
    successors=defaultdict(set)
    for dest,preds in graph.items():
        for source in preds:successors[source].add(dest)
    seen=[];node=start
    while node!=target:
        if node in seen or len(seen)>=64:
            raise ValueError('Upstream selected fanout cycles or exceeds bound')
        seen.append(node)
        if len(successors[node])!=1:
            raise ValueError('Upstream selector has other selected consumers or a dead end')
        node=next(iter(successors[node]))
    if successors[target]:raise ValueError('LUT input has unexpected selected routing fanout')
    return seen+[target]


def prove_upstream(tile,lut,index,selector_tile,feature,spec,modules,state,features,words,pips,enabled):
    kind=state['tiles']['Tile_'+tile+'_LUT4x8_ha']['tile_type']
    init,mode=prove_lut_independent(tile,lut,index,spec,modules[kind],state,features,words,
                                   allow_registered=True)
    cofactor=dict(observed_init=init,cofactor_addresses_checked=16,observed_ff_select=mode,
                  scope='Binary function independence only; the existing LUT input selector is preserved.')
    entries=spec['TileSpecs'][selector_tile]
    mapping=entries[feature]
    if len(mapping)!=1 or list(mapping.values())!=['1']:
        raise ValueError('Require one existing positive selector bit')
    address=next(iter(mapping));source,dest=feature.split('.')
    alternatives=[(k,v) for k,v in entries.items() if k.endswith('.'+dest)]
    if (len(alternatives)!=2 or {tuple(v.items()) for k,v in alternatives}
            !={((address,'0'),),((address,'1'),)}):
        raise ValueError('Require an existing two-way selector')
    if any(f.split('.')[0]==selector_tile and address in entries[f.split('.',1)[1]] for f in features):
        raise ValueError('Upstream selector overlaps an active feature')
    if any(address in mp for key,mp in entries.items()
           if any(key.startswith(letter+'.') for letter in 'ABCDEFGH')):
        raise ValueError('Upstream selector overlaps primitive state/control fields')
    matches=[(n,r) for n,r in state['tiles'].items() if n.split('_')[1]==selector_tile]
    if len(matches)!=1:raise ValueError('Missing unique selector tile')
    native,row=matches[0];module=modules[row['tile_type']];name,cell=latch(module,address)
    selector=module['netnames']['Inst_'+row['tile_type']+'_switch_matrix.inst_cus_mux21_'+dest+'.S']['bits']
    if cell['connections']['Q']!=selector or row['q'][name]!='0':
        raise ValueError('Actual upstream selector identity/value differs')
    x,y=map(int,selector_tile[1:].split('Y'));frame,offset=divmod(address,32)
    word=1+(x*20+frame)*6+1+(4-y)
    if words[word]>>offset&1:raise ValueError('Upstream image selector is not zero')
    graph=selected_predecessors(spec,words,pips);target=(tile,'L'+lut+'_I'+str(index))
    if index in (1,2):carry_cone(graph,tile,lut,enabled)
    chain=isolated_chain(graph,(selector_tile,dest),target)
    before=trace_route(graph,target)
    if (selector_tile,dest) not in before:raise ValueError('Selector is outside the selected input route')
    candidate=list(words);candidate[word]|=1<<offset
    after_graph=selected_predecessors(spec,candidate,pips)
    if isolated_chain(after_graph,(selector_tile,dest),target)!=chain:
        raise ValueError('Selected downstream consumers changed')
    after=trace_route(after_graph,target)
    if after==before or (selector_tile,source) not in after:
        raise ValueError('Alternate route was not selected')
    if index in (1,2):carry_cone(after_graph,tile,lut,enabled)
    return dict(tile=native,cell=name,tile_bit=address,word=word,word_bit=offset,
                before='0',after='1',feature=selector_tile+'.'+feature,
                target=[tile,lut,index],cofactor_proof=cofactor,
                selected_downstream_nodes=chain,route_before=before,route_after=after,
                scope='Only one binary-independent LUT input changes. No native initialization, reload or timing acceptance.')

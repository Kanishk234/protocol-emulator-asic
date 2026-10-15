"""Audit every bounded post-antenna identity-buffer batch and antenna interval."""
import json
from pathlib import Path
import re
from event_nor2_screen import logical_cells,validate_antenna_only_changes
from electrical_repair_plan import validate_change,expanded_pins


def validate_batch(before,after,proposal,iteration,reviewed_sources=None):
    if set(proposal)!={'groups'} or not isinstance(proposal['groups'],list):raise ValueError('Invalid post-antenna receipt')
    groups=proposal['groups']
    if iteration not in (0,1) or not 1<=len(groups)<=32:raise ValueError('Post-antenna batch exceeds reviewed budget')
    cells={}
    normalize=lambda value:value.strip().removeprefix('\\')
    for name,(master,pins) in logical_cells(before).items():
        cells[normalize(name)]=(master,expanded_pins(master,pins))
    sources={};moved=set()
    for group in groups:
        if set(group)!={'buffer','net','source_net','master','sinks'}:raise ValueError('Unexpected post-antenna group fields')
        if group['master']!='sg13cmos5l_buf_4' or not re.fullmatch(f'tripwire_postant_{iteration}_[0-9]+',group['buffer']):raise ValueError('Unreviewed post-antenna cell')
        if group['net']!=group['buffer']+'_net' or not 1<=len(group['sinks'])<=4:raise ValueError('Invalid post-antenna branch')
        source=group['source_net'];attached=[];drivers=[]
        for name,(master,pins) in cells.items():
            for pin,value in pins:
                if value.strip().removeprefix('\\')!=source:continue
                attached.append((name,pin))
                if pin in ('X','Y','Q'):drivers.append((name,pin,master))
                if pin in ('CLK','GCLK','GATE','RESET_B'):raise ValueError('Protected post-antenna source')
        if len(drivers)!=1 or (len(attached)-1<=8 and source not in (reviewed_sources or ())) or not drivers[0][2].startswith('sg13cmos5l_'):
            raise ValueError('Source is not a unique overloaded standard-cell data net')
        sources.setdefault(source,set())
        for sink in group['sinks']:
            pair=tuple(sink)
            if pair in moved or pair not in attached or pair==drivers[0][:2]:raise ValueError('Wrong or repeated post-antenna sink')
            moved.add(pair);sources[source].add(pair)
    for source,sinks in sources.items():
        attached={(n,p) for n,(m,pins) in cells.items() for p,v in pins if v.strip().removeprefix('\\')==source and p not in ('X','Y','Q')}
        if sinks!=attached:raise ValueError('Incomplete post-antenna load partition')
        if sum(g['source_net']==source for g in groups)>8:raise ValueError('Post-antenna driver still overloaded')
    validate_change(before,after,proposal)
    return len(groups)


def audit(before,after,root,log,margin_audit=None):
    root=Path(root);receipts=sorted(root.glob('postant_*.json'))
    if len(receipts)>2:raise ValueError('Too many post-antenna batches')
    match=re.findall(r'TRIPWIRE post-antenna fanout: converged after (\d+) batches',log)
    if match!=[str(len(receipts))]:raise ValueError('Missing post-antenna convergence receipt')
    total=0;previous=before
    for iteration,path in enumerate(receipts):
        if path.name!=f'postant_{iteration}.json':raise ValueError('Noncontiguous post-antenna history')
        first=(root/f'postant_{iteration}.before.nl.v').read_text()
        last=(root/f'postant_{iteration}.after.nl.v').read_text()
        validate_antenna_only_changes(previous,first)
        reviewed=margin_audit(root,iteration) if margin_audit is not None else None
        count=validate_batch(first,last,json.loads(path.read_text()),iteration,reviewed)
        if f'TRIPWIRE post-antenna fanout: batch {iteration} added {count} BUF4 cells' not in log:
            raise ValueError('Post-antenna batch log mismatch')
        total+=count;previous=last
    validate_antenna_only_changes(previous,after)
    return dict(post_antenna_batches=len(receipts),post_antenna_buffers=total,
        maximum_post_antenna_buffers=64,post_antenna_connectivity_audited=True)

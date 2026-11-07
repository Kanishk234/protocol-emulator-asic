"""Replay saved local planning inputs without OpenROAD; never qualify physical timing."""
import argparse
import hashlib
import json
from pathlib import Path
from local_route_patch import edge, patch, audit


def replay(root):
    root=Path(root)
    source=root/'planning_inputs.json';capacity=root/'probe_grid.json'
    data=json.loads(source.read_text())
    if data['capacity_input']!='probe_grid.json':raise ValueError('Unexpected capacity input')
    free={}
    for a,b,cap,used in json.loads(capacity.read_text()):
        if any(type(v) is not int or v<0 for v in (cap,used)):
            raise ValueError('Invalid measured capacity or usage')
        e=edge(a,b)
        if e in free:raise ValueError('Duplicate capacity edge')
        free[e]=cap-used
    changed,ledger,remaining=patch(data['routes'],free,data['detours'],data['attachments'])
    audit(data['routes'],{**data['routes'],**changed},ledger)
    return dict(changed_nets=sorted(changed),detours=len(data['detours']),
        attachments=len(data['attachments']),minimum_remaining_headroom=min(remaining.values()),
        input_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (source,capacity)},
        physical_qualified=False,timing_measured=False,scope='Offline planning replay only')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    args=parser.parse_args()
    print(json.dumps(replay(args.directory),indent=2))

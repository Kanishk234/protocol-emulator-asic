"""Exact geometry audit of OpenROAD segment exports, not timing or signoff."""
import argparse
import json
from pathlib import Path


def parse(text):
    nets={};name=None;opened=False
    for raw in text.splitlines():
        line=raw.strip()
        if not line: continue
        if line=='(':
            if name is None or opened: raise ValueError('Unexpected route opening')
            opened=True
        elif line==')':
            if not opened or not nets[name]: raise ValueError('Empty or malformed route')
            opened=False;name=None
        elif not opened:
            if name is not None or len(line.split())!=1 or line in nets:
                raise ValueError('Malformed or duplicate route name')
            name=line;nets[name]=[]
        else:
            fields=line.split()
            if len(fields)!=6: raise ValueError('Wrong route segment width')
            x1,y1,layer1,x2,y2,layer2=fields
            try: a=(int(x1),int(y1),layer1);b=(int(x2),int(y2),layer2)
            except ValueError: raise ValueError('Noninteger route coordinate') from None
            if sum(u!=v for u,v in zip(a,b))>1: raise ValueError('Nonorthogonal route segment')
            # Direction and output order do not change geometry; duplicates do.
            nets[name].append(tuple(sorted((a,b))))
    if name is not None or opened or not nets: raise ValueError('Incomplete route export')
    return {n:tuple(sorted(s)) for n,s in nets.items()}


def compare(before,after,allowed=()):
    old,new=parse(before),parse(after);allowed=set(allowed)
    changed={n for n in set(old)|set(new) if old.get(n)!=new.get(n)}
    unexpected=changed-allowed
    return dict(old_routed_nets=len(old),new_routed_nets=len(new),changed_nets=sorted(changed),
        unexpected_changed_nets=sorted(unexpected),unchanged_routes_preserved=not unexpected,
        exact_roundtrip=not changed,physical_timing_measured=False,official_signoff=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('before',type=Path);p.add_argument('after',type=Path)
    p.add_argument('--allowed-net',action='append',default=[])
    a=p.parse_args();result=compare(a.before.read_text(),a.after.read_text(),a.allowed_net)
    print(json.dumps(result,indent=2))
    if not result['unchanged_routes_preserved']: raise SystemExit(1)

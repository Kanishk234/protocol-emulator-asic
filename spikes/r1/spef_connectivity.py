"""Independent resistor-graph check; a CONN entry alone is not annotation."""
from collections import Counter
import math
import re


def inspect_spef(text):
    if text.count('*NAME_MAP\n')!=1 or '*D_NET ' not in text:
        raise ValueError('Unsupported or empty SPEF')
    names={}
    for line in text.split('*NAME_MAP\n',1)[1].split('*PORTS',1)[0].split('*D_NET ',1)[0].splitlines():
        parts=line.split()
        if not parts:continue
        if len(parts)!=2 or not re.fullmatch(r'\*\d+',parts[0]) or parts[0] in names:
            raise ValueError('Invalid SPEF name map')
        names[parts[0]]=parts[1]
    bad=[];histogram=Counter();nets=0;terminals=0
    for block in text.split('*D_NET ')[1:]:
        lines=block.splitlines();net=lines[0].split()[0];parent={};pins=[];section=None;complete=False
        def find(node):
            parent.setdefault(node,node)
            root=node
            while parent[root]!=root:root=parent[root]
            while parent[node]!=node:
                nxt=parent[node];parent[node]=root;node=nxt
            return root
        for line in lines[1:]:
            parts=line.split()
            if not parts:continue
            if parts[0]=='*END':complete=True;break
            if parts[0] in ('*CONN','*CAP','*RES'):section=parts[0];continue
            if section=='*CONN':
                if parts[0] not in ('*I','*P') or len(parts)<3:
                    raise ValueError('Unknown SPEF connection record')
                pins.append(parts[1])
            elif section=='*RES':
                if len(parts)!=4 or not math.isfinite(float(parts[3])) or float(parts[3])<0:
                    raise ValueError('Invalid SPEF resistor record')
                parent[find(parts[1])]=find(parts[2])
        if not complete or len(pins)!=len(set(pins)):
            raise ValueError('Incomplete or duplicate SPEF terminal evidence')
        components=len({find(pin) for pin in pins});histogram[components]+=1
        nets+=1;terminals+=len(pins)
        if components>1:
            bad.append(dict(net=names.get(net,net),terminals=len(pins),terminal_components=components))
    return dict(passed=not bad,nets=nets,terminals=terminals,
                terminal_component_histogram=dict(sorted(histogram.items())),disconnected_nets=bad,
                scope='Every named CONN terminal must share a resistor-graph component within its D_NET. Not geometry/LVS or configured timing acceptance.')

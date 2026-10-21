"""Third bounded R1 topology: eight-choice escape, two-choice local selection.

Structural policy only: no workload identities, placements or seed search.
Each original cell output retains an escape into every cardinal jump bank.
Clock/reset/enable/carry and primitive input selectors are left unchanged.
"""
from collections import defaultdict
import re

from profiling.track_screen import GLOBAL

ESCAPE = re.compile(r'^J([NESW])2BEG([0-7])$')
GATHER = re.compile(r'^J(?:2MID_(?:AB|CD|EF|GH)[ab]|2END_(?:AB|CD|EF|GH)|_l_(?:AB|CD|EF|GH))_BEG([0-3])$')
LUT_INPUT = re.compile(r'^L([A-H])_I([0-3])$')


def rotate(values, start):
    values=sorted(values)
    if not values:
        return []
    start %= len(values)
    return values[start:]+values[:start]


def cover_outputs(choices, budget=4):
    """Bipartite matching covers every source using budget slots per destination."""
    if budget < 1 or any(not values for values in choices.values()):
        raise ValueError('Invalid escape budget or empty source group')
    candidates=defaultdict(list)
    for destination,values in sorted(choices.items()):
        for source in sorted(set(values)):
            candidates[source].extend((destination,i) for i in range(budget))
    owner={}
    def assign(source, seen):
        for slot in candidates[source]:
            if slot in seen:
                continue
            seen.add(slot)
            if slot not in owner or assign(owner[slot],seen):
                owner[slot]=source
                return True
        return False
    for source in sorted(candidates,key=lambda s:(len(candidates[s]),s)):
        if not assign(source,set()):
            raise ValueError('Escape radix cannot cover every original cell output')
    selected={destination:set() for destination in choices}
    for (destination,_),source in owner.items():
        selected[destination].add(source)
    for index,(destination,values) in enumerate(sorted(choices.items())):
        for source in rotate(values,index):
            if len(selected[destination]) < budget:
                selected[destination].add(source)
    return {destination:sorted(values) for destination,values in selected.items()}


def reduce(connections):
    result={destination:sorted(set(sources)) for destination,sources in connections.items()}
    if any(not sources for sources in result.values()):
        raise ValueError('Empty selector')
    escape_groups=defaultdict(dict)
    for destination,sources in result.items():
        if match:=ESCAPE.fullmatch(destination):
            escape_groups[match[1]][destination]=[s for s in sources if not GLOBAL.fullmatch(s)]
    coverage={}
    for direction,group in sorted(escape_groups.items()):
        local=cover_outputs(group)
        before=set().union(*(set(values) for values in group.values()))
        after=set().union(*(set(values) for values in local.values()))
        if before != after:
            raise ValueError('Cell-output escape coverage changed')
        coverage[direction]=sorted(after)
        for destination,values in local.items():
            index=int(ESCAPE.fullmatch(destination)[2])
            routing=[s for s in result[destination] if GLOBAL.fullmatch(s)]
            result[destination]=sorted(values+rotate(routing,'NESW'.index(direction)+index)[:4])
            if len(result[destination]) > 8:
                raise ValueError('Escape mux exceeds eight choices')
    changed=[]
    for destination,sources in list(result.items()):
        if match:=GATHER.fullmatch(destination):
            local=[s for s in sources if not GLOBAL.fullmatch(s)]
            routing=[s for s in sources if GLOBAL.fullmatch(s)]
            if len(local)>1:
                raise ValueError('Unexpected local gather structure')
            result[destination]=sorted(local+rotate(routing,int(match[1]))[:2-len(local)])
        elif match:=LUT_INPUT.fullmatch(destination):
            cell=ord(match[1])-ord('A')
            # Paired LUTs select complementary halves, keeping every shared
            # gather output connected rather than leaving dead config state.
            offset=(cell%2)*2+cell//2+int(match[2])
            result[destination]=sorted(rotate(sources,offset)[:2])
        if set(result[destination]) != set(connections[destination]):
            changed.append(destination)
        if not result[destination] or not set(result[destination]) <= set(connections[destination]):
            raise ValueError('Reduced selector invents or loses all inputs')
    bits=sum((len(sources)-1).bit_length() for sources in result.values())
    return result,dict(policy='radix8_2',select_bits=bits,changed_outputs=sorted(changed),
                       cell_output_coverage_per_direction=coverage,
                       physical_acceptance=False,timing_acceptance=False,
                       scope='Structural reduced-radix proposal; coverage is not complete routability or functional proof.')

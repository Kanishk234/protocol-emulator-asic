"""Propose global-track folding while preserving eight-way local jump wiring.

Pure graph/cost screen only. A candidate needs CSV/RTL regeneration, real PNR,
bitstream operation and physical measurements before any acceptance.
"""
from collections import defaultdict
import re

GLOBAL = re.compile(r'^([NESW](?:1BEG|1END|2BEGb|2BEG|2END|2MID))([0-9]+)$')


def fold_pin(name, tracks):
    if tracks not in (4,6,8):
        raise ValueError('Declared screens use 4,6,8 global tracks')
    match=GLOBAL.fullmatch(name)
    if not match:
        return name
    index=int(match[2])
    if index>=8:
        raise ValueError('Unexpected original track index')
    return match[1]+str(index%tracks)


def screen(connections, tracks):
    # Validate even an empty graph; pin traversal must not control validation.
    fold_pin('', tracks)
    if not connections:
        raise ValueError('Empty switch matrix')
    folded=defaultdict(set)
    for destination,sources in connections.items():
        if not sources:
            raise ValueError('Empty switch output')
        for source in sources:
            folded[fold_pin(destination,tracks)].add(fold_pin(source,tracks))
    proposal={k:sorted(v) for k,v in sorted(folded.items())}
    bits=sum((len(v)-1).bit_length() for v in proposal.values())
    max_fanin=max(map(len,proposal.values()),default=0)
    return dict(connections=proposal,global_tracks=tracks,select_bits=bits,
                max_fanin=max_fanin,custom_mux_arity_supported=max_fanin<=16,
                local_jump_tracks_unchanged=True,physical_acceptance=False,
                timing_acceptance=False,
                scope='Connection folding proposal only; graph aliases become mux choices, never wired-OR. Requires regenerated ports, mux/config RTL and full workload/physical validation.')

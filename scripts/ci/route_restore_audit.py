"""No-edit route restoration acceptance, independent of electrical closure."""
import math
from event_nor2_screen import logical_cells
from postgrt_timing import CORNERS
from route_segment_audit import compare


def audit_geometry_and_logic(original_segments,restored_segments,noop_segments,before_nl,after_nl):
    for target in (restored_segments,noop_segments):
        if not compare(original_segments,target)['exact_roundtrip']:
            raise ValueError('No-edit restoration changes route geometry')
    if logical_cells(before_nl)!=logical_cells(after_nl):
        raise ValueError('No-edit restoration changes netlist')
    return dict(exact_segment_roundtrip=True,unchanged_routes_preserved=True,
                unchanged_netlist=True,physical_change_applied=False,official_signoff=False)


def audit_timing(comparison):
    if set(comparison.get('corners',{}))!=set(CORNERS): raise ValueError('Missing timing corners')
    for c in CORNERS:
        before=comparison['corners'][c]['before'];after=comparison['corners'][c]['after']
        for kind in ('setup','hold'):
            key=f'timing__{kind}__ws__corner:{c}'
            a,b=before.get(key),after.get(key)
            if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (a,b)) or abs(a-b)>1e-6:
                raise ValueError('Restoration changes setup/hold timing')
        for kind in ('slew','fanout','cap'):
            key=f'design__max_{kind}_violation__count__corner:{c}'
            if key not in before or key not in after or before[key]!=after[key]:
                raise ValueError('Restoration changes electrical measurements')
    return True

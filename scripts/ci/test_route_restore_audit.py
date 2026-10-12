import copy
import pytest
from route_restore_audit import audit_geometry_and_logic,audit_timing
from postgrt_timing import CORNERS

S='n\n(\n0 0 Metal2 10 0 Metal2\n)\n'
N='sg13cmos5l_buf_1 cell (.A(a), .X(b));'


def test_exact_no_edit_geometry_and_logic():
    x=audit_geometry_and_logic(S,S,S,N,N)
    assert x['exact_segment_roundtrip'] and not x['official_signoff']


@pytest.mark.parametrize('fault',['restore','noop','netlist'])
def test_hidden_geometry_or_logic_changes_refused(fault):
    restored=noop=S;after=N
    if fault=='restore': restored=S.replace('10','20')
    elif fault=='noop':noop=S.replace('10','20')
    else:after=N.replace('.X(b)','.X(other)')
    with pytest.raises(ValueError):audit_geometry_and_logic(S,restored,noop,N,after)


def timing():
    x={'corners':{}}
    for c in CORNERS:
        m={f'timing__setup__ws__corner:{c}':0,f'timing__hold__ws__corner:{c}':.056771}
        m.update({f'design__max_{k}_violation__count__corner:{c}':3 for k in ('slew','fanout','cap')})
        x['corners'][c]={'before':m,'after':copy.deepcopy(m)}
    return x


def test_matched_timing_does_not_require_electrical_closure(): assert audit_timing(timing())


@pytest.mark.parametrize('fault',['timing','electrical','missing','nan'])
def test_unmatched_measurements_refused(fault):
    x=timing();c=CORNERS[0];m=x['corners'][c]['after']
    if fault=='timing':m[f'timing__hold__ws__corner:{c}']+=.001
    elif fault=='electrical':m[f'design__max_slew_violation__count__corner:{c}']+=1
    elif fault=='missing':m.pop(f'design__max_cap_violation__count__corner:{c}')
    else:m[f'timing__hold__ws__corner:{c}']=float('nan')
    with pytest.raises(ValueError):audit_timing(x)

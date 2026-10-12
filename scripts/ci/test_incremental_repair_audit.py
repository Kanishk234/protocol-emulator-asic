import pytest
from incremental_repair_audit import audit,added_antenna_nets,require_live_demand

D='COMPONENTS 1 ;\n- old sg13cmos5l_buf_1 + PLACED ( 0 0 ) N ;\nEND COMPONENTS'
S='net\n(\n0 0 Metal2 10 0 Metal2\n)\n'
P={'groups':[{'source_net':'net','net':'branch'}]}


def test_only_planned_route_edits_allowed_and_old_placements_fixed():
    x=audit(D,D,S,S.replace('10','20'),P)
    assert x['unchanged_routes_preserved']
    with pytest.raises(ValueError):audit(D,D.replace('( 0 0 )','( 1 0 )'),S,S,P)
    with pytest.raises(ValueError):audit(D,D,S,S+S.replace('net','other'),P)


def test_antenna_route_allowance_requires_antenna_only_netlist_addition():
    old='sg13cmos5l_buf_1 old (.A(in), .X(net));'
    new=old+' sg13cmos5l_antennanp diode (.A(net));'
    assert added_antenna_nets(old,new)==['net']
    with pytest.raises(ValueError):added_antenna_nets(old,new.replace('.A(in)','.A(other)'))


@pytest.mark.parametrize('fault',['none','zero_initial','zero_final','missing'])
def test_live_demand_is_required_before_and_after_edits(fault):
    values=[100,102]
    if fault=='zero_initial':values[0]=0
    elif fault=='zero_final':values[1]=0
    elif fault=='missing':values=values[:1]
    text='\n'.join('Final congestion report:\nTotal 1000 '+str(v)+' 10.0% 0 / 0 / 0' for v in values)
    if fault=='none':assert require_live_demand(text)
    else:
        with pytest.raises(ValueError):require_live_demand(text)

from copy import deepcopy
import pytest
from autonomy import capacity_cut as cut,corridor_solver as model


def graph(capacity=4,demand=1):
    return dict(schema_version=2,
        contract=dict(model.CONTRACT,boundary=model.EXTERIOR_BOUNDARY,exterior_connectivity=model.EXTERIOR_CONTRACT,
            vias='forbidden',nonpreferred='explicit_edges',omitted_constraints=sorted(model.REQUIRED_OMISSIONS)),
        provenance=dict(kind='abstract_fixture',description='five independent nets cross a four-unit edge',source_sha256=None),
        layers=[dict(id='M1',preferred_direction='horizontal')],
        nodes=[dict(id='left',x=0,y=0,layer='M1'),dict(id='right',x=1,y=0,layer='M1')],
        edges=[dict(id='crossing',u='left',v='right',direction='horizontal',capacity=capacity,fixed_usage=0)],
        nets=[dict(id=str(i),terminals=['left','right'],boundary_terminals=['left','right'],
            frozen_exterior_components=[],track_demand_by_layer={'M1':demand},via_track_demand=None,
            allowed_planar_layers=['M1']) for i in range(5)])


def test_five_required_crossings_exceed_four_units_without_solver(monkeypatch):
    monkeypatch.setattr(model,'solve',lambda *a,**k:pytest.fail('No solver permitted'))
    r=cut.certify(graph(),axis='x',coordinate=0)
    assert r['residual_crossing_capacity']==4 and r['required_crossing_demand_lower_bound']==5
    assert r['independently_verified_graph_infeasible']
    assert not r['native_inputs_authenticated'] and not r['physical_acceptance']


def test_capacity_and_fixed_usage_have_exact_units():
    g=graph(capacity=5)
    assert not cut.certify(g,axis='x',coordinate=0)['independently_verified_graph_infeasible']
    g['edges'][0]['fixed_usage']=1
    assert cut.certify(g,axis='x',coordinate=0)['independently_verified_graph_infeasible']
    r=cut.certify(graph(capacity=9,demand=2),axis='x',coordinate=0)
    assert r['required_crossing_demand_lower_bound']==10 and r['independently_verified_graph_infeasible']


def test_private_exterior_can_bypass_physical_cut_and_prevents_certificate():
    g=graph();g['nets'][0]['frozen_exterior_components']=[['left','right']]
    with pytest.raises(ValueError,match='exterior connectivity crosses'):
        cut.certify(g,axis='x',coordinate=0)


def test_invalid_zero_demand_rejected_and_unseparated_terminals_do_not_prove_infeasible():
    with pytest.raises(ValueError):cut.certify(graph(demand=0),axis='x',coordinate=0)
    assert not cut.certify(graph(),axis='y',coordinate=0)['independently_verified_graph_infeasible']


@pytest.mark.parametrize('axis,coordinate',[('z',0),('x',True),('y',0.5)])
def test_invalid_partition_rejected(axis,coordinate):
    with pytest.raises(ValueError):cut.certify(graph(),axis=axis,coordinate=coordinate)


def test_fixed_violation_does_not_masquerade_as_this_certificate():
    g=graph();g['edges'][0]['fixed_usage']=5
    with pytest.raises(ValueError,match='separate certificate'):cut.certify(g,axis='x',coordinate=0)


def test_certificate_does_not_mutate_graph():
    g=graph();before=deepcopy(g)
    assert cut.certify(g,axis='x',coordinate=0)==cut.certify(g,axis='x',coordinate=0)
    assert g==before

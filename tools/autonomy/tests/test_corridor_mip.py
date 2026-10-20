"""SCIP small-graph qualification, never actual WARP model execution."""
from copy import deepcopy
import importlib.util
import itertools
import math

import pytest

from autonomy import corridor_mip as mip, corridor_solver as model
from autonomy.tests.test_corridor_solver import graph, version2, brute_feasible

requires_solver = pytest.mark.skipif(importlib.util.find_spec('ortools') is None,
                                    reason='optional requirements-routing.txt not installed')


@requires_solver
@pytest.mark.parametrize('schema', [1, 2])
@pytest.mark.parametrize('capacities', list(itertools.product(range(3), repeat=3)))
def test_mip_matches_independent_edge_subset_oracle(schema, capacities):
    g = graph() if schema == 1 else version2()
    g['nets'][0].update(terminals=['a', 'c', 'd'], boundary_terminals=['a', 'c', 'd'])
    if schema == 2:
        g['nets'][0]['frozen_exterior_components'] = [['a', 'c']]
    other = deepcopy(g['nets'][0]); other.update(id='other', terminals=['c', 'd'], boundary_terminals=['c', 'd'])
    if schema == 2:
        other['frozen_exterior_components'] = []
    g['nets'].append(other)
    for edge, capacity in zip(g['edges'], capacities):
        edge['capacity'] = capacity
    expected = 'FEASIBLE' if brute_feasible(g) else 'INFEASIBLE'
    r = mip.solve(g)
    assert r['status'] == expected
    assert not r['native_inputs_authenticated'] and not r['physical_acceptance']
    assert not r['infeasibility_independently_certified']
    assert r['model_size']['binary_occupancy_variables'] == 6
    if expected == 'FEASIBLE':
        assert model.validate_witness(g, r['witness']) == r['witness_check']


@requires_solver
def test_private_exterior_connectivity_never_leaks_between_nets():
    g = version2(); g['edges'] = []
    g['nets'][0]['frozen_exterior_components'] = [['a', 'c']]
    assert mip.solve(g)['witness'] == {'n': []}
    other = deepcopy(g['nets'][0]); other.update(id='other', frozen_exterior_components=[])
    g['nets'].append(other)
    assert mip.solve(g)['status'] == 'INFEASIBLE'


@requires_solver
def test_shared_trunk_charges_occupancy_once_and_keeps_fixed_use():
    g = graph(); g['nets'][0]['terminals'] = ['a', 'c', 'd']
    assert mip.solve(g)['status'] == 'FEASIBLE'
    g['edges'][0]['fixed_usage'] = 1
    assert mip.solve(g)['status'] == 'INFEASIBLE'


@requires_solver
def test_per_layer_demand_and_forbidden_planar_layers():
    g = graph(); g['nets'][0]['track_demand_by_layer']['M1'] = 2
    assert mip.solve(g)['status'] == 'INFEASIBLE'
    for edge in g['edges']: edge['capacity'] = 2
    assert mip.solve(g)['status'] == 'FEASIBLE'
    g['layers'].append({'id': 'M2', 'preferred_direction': 'vertical'})
    g['nets'][0]['track_demand_by_layer']['M2'] = 1
    g['nets'][0]['allowed_planar_layers'] = ['M2']
    assert mip.solve(g)['status'] == 'INFEASIBLE'


@requires_solver
@pytest.mark.parametrize('coarse', [False, True])
def test_explicit_vias_keep_zero_or_positive_declared_demand(coarse):
    g = graph(); g['layers'].append({'id': 'M2', 'preferred_direction': 'vertical'})
    g['nodes'] = [g['nodes'][0], dict(id='top', x=0, y=0, layer='M2')]
    g['contract']['vias'] = 'unlimited_coarse_edges' if coarse else 'explicit_capacity_edges'
    g['edges'] = [dict(id='via', u='a', v='top', direction='via', capacity=None if coarse else 1, fixed_usage=0)]
    g['nets'][0].update(terminals=['a', 'top'], boundary_terminals=[], track_demand_by_layer={'M1': 1, 'M2': 2},
                         via_track_demand=0 if coarse else 1)
    assert mip.solve(g)['status'] == 'FEASIBLE'
    if not coarse:
        g['edges'][0]['capacity'] = 0
        assert mip.solve(g)['status'] == 'INFEASIBLE'


@requires_solver
def test_known_five_required_crossings_exceed_four_units():
    g = graph(); g['edges'] = [dict(id='ac', u='a', v='c', direction='horizontal', capacity=4, fixed_usage=0)]
    g['nets'] = [dict(deepcopy(g['nets'][0]), id=str(i)) for i in range(5)]
    assert mip.solve(g)['status'] == 'INFEASIBLE'


@requires_solver
def test_private_variables_limits_and_deterministic_model_identity():
    g = version2(); g['edges'] = []; g['nets'][0]['frozen_exterior_components'] = [['a', 'c']]
    r = mip.solve(g, max_variables=1)
    assert r['model_size']['variables'] == 1 and r['model_size']['continuous_connectivity_variables'] == 1
    assert r['model_sha256'] == mip.solve(g)['model_sha256']
    g['nets'][0]['terminals'] = ['a', 'c', 'd'];g['nets'][0]['boundary_terminals'] = ['a', 'c', 'd']
    g['nets'][0]['frozen_exterior_components'] = [['a', 'c', 'd']]
    with pytest.raises(model.InputError, match='variables'): mip.solve(g, max_variables=1)


@pytest.mark.parametrize('kwargs', [dict(max_seconds=0), dict(max_seconds=math.inf), dict(max_memory_mb=True),
                                   dict(max_memory_mb=4097), dict(max_variables=0)])
def test_limit_validation_precedes_backend(kwargs):
    with pytest.raises(model.InputError): mip.solve(graph(), **kwargs)


@pytest.mark.parametrize('value', [0.1, 0.5, 1.01, -0.01, math.nan, math.inf])
def test_ambiguous_occupancy_rejected(value):
    with pytest.raises(RuntimeError, match='occupancy'): mip._occupancy(value)


def test_only_close_binary_values_are_normalized():
    assert mip._occupancy(1e-8) == 0 and mip._occupancy(1 - 1e-8) == 1


@requires_solver
@pytest.mark.parametrize('status,expected', [('OPTIMAL', 'FEASIBLE'), ('FEASIBLE', 'FEASIBLE'),
                                           ('INFEASIBLE', 'INFEASIBLE'), ('NOT_SOLVED', 'UNKNOWN')])
def test_native_status_scope(status, expected):
    from ortools.linear_solver import pywraplp
    assert mip._status(getattr(pywraplp.Solver, status), pywraplp.Solver) == expected


@requires_solver
@pytest.mark.parametrize('status', ['ABNORMAL', 'UNBOUNDED', 'MODEL_INVALID'])
def test_native_errors_never_become_infeasible(status):
    from ortools.linear_solver import pywraplp
    with pytest.raises(RuntimeError): mip._status(getattr(pywraplp.Solver, status), pywraplp.Solver)


@requires_solver
def test_wrong_package_version_fails_instead_of_skip(monkeypatch):
    import ortools
    monkeypatch.setattr(ortools, '__version__', 'wrong')
    with pytest.raises(RuntimeError, match='Require ortools'): mip.solve(graph())


@requires_solver
def test_missing_scip_fails_without_fallback(monkeypatch):
    from ortools.linear_solver import pywraplp
    monkeypatch.setattr(pywraplp.Solver, 'CreateSolver', lambda _: None)
    with pytest.raises(RuntimeError, match='unavailable'): mip.solve(graph())


@requires_solver
@pytest.mark.parametrize('failure', ['version', 'threads', 'memory', 'not_solved'])
def test_failed_backend_configuration_and_no_incumbent(monkeypatch, failure):
    from ortools.linear_solver import pywraplp
    s = pywraplp.Solver.CreateSolver('SCIP')
    if failure == 'version': s.SolverVersion = lambda: 'SCIP wrong'
    if failure == 'threads': s.SetNumThreads = lambda _: False
    if failure == 'memory': s.SetSolverSpecificParametersAsString = lambda _: False
    s.Solve = lambda: pywraplp.Solver.NOT_SOLVED
    monkeypatch.setattr(pywraplp.Solver, 'CreateSolver', lambda _: s)
    if failure == 'not_solved':
        r = mip.solve(graph())
        assert r['status'] == 'UNKNOWN' and r['witness'] is None and r['witness_check'] is None
    else:
        with pytest.raises(RuntimeError): mip.solve(graph())


@requires_solver
def test_accepted_incumbent_still_requires_independent_connectivity_check(monkeypatch):
    monkeypatch.setattr(mip, '_occupancy', lambda _: 0)
    with pytest.raises(model.InputError, match='disconnected'):
        mip.solve(graph())


@requires_solver
def test_graph_copy_and_single_terminal_need_no_occupied_edges():
    g = graph(); g['edges'] = []; g['nets'][0].update(terminals=['a'], boundary_terminals=[])
    before = deepcopy(g)
    result = mip.solve(g)
    assert g == before and result['status'] == 'FEASIBLE'
    assert result['witness'] == {'n': []}

"""Bounded SCIP feasibility of the declared corridor graph, never native routing.

Occupancy stays binary; connectivity flow is continuous. Independent integer
resource/BFS witness validation remains mandatory. No package install or EDA.
"""
from __future__ import annotations

from collections import defaultdict
import math

from autonomy import corridor_solver as graph_model

SOLVER_VERSION = '9.14.6206'
SCIP_VERSION_PREFIX = 'SCIP 9.2.2 '
INTEGRAL_TOLERANCE = 1e-6


def _occupancy(value):
    if (not math.isfinite(value) or
            min(abs(value), abs(value - 1)) > INTEGRAL_TOLERANCE):
        raise RuntimeError('SCIP returned ambiguous/nonbinary occupancy')
    return int(value >= 0.5)


def _status(status, api):
    if status in (api.OPTIMAL, api.FEASIBLE):
        return 'FEASIBLE'
    if status == api.INFEASIBLE:
        return 'INFEASIBLE'
    if status == api.NOT_SOLVED:
        return 'UNKNOWN'
    raise RuntimeError('Unexpected SCIP result; no feasibility conclusion')


def solve(graph, *, max_seconds=30, max_memory_mb=1024, max_variables=100_000):
    """One-thread binary/continuous MIP; limits are not an OS memory sandbox."""
    graph = graph_model.validate_graph(graph)
    max_seconds = graph_model._limit(max_seconds, 'max_seconds', 300)
    graph_model._integer(max_memory_mb, 'max_memory_mb', 1, 4096)
    graph_model._integer(max_variables, 'max_variables', 1, graph_model.MAX_VARIABLES)
    private_count = sum(len(c) - 1 for n in graph['nets']
                        for c in n.get('frozen_exterior_components', ()))
    count = 2 * len(graph['edges']) * len(graph['nets']) + private_count
    if count > max_variables:
        raise graph_model.InputError(f'model requires {count} variables, exceeds limit {max_variables}')
    try:
        import ortools
        from ortools.linear_solver import pywraplp
    except ImportError as exc:
        raise RuntimeError('Optional routing solver missing; install requirements-routing.txt in project venv') from exc
    if ortools.__version__ != SOLVER_VERSION:
        raise RuntimeError(f'Require ortools=={SOLVER_VERSION}, found {ortools.__version__}')
    solver = pywraplp.Solver.CreateSolver('SCIP')
    if solver is None:
        raise RuntimeError('Pinned SCIP backend unavailable')
    version = solver.SolverVersion()
    if not version.startswith(SCIP_VERSION_PREFIX):
        raise RuntimeError(f'Require SCIP9.2.2, found {version}')
    if not solver.SetNumThreads(1):
        raise RuntimeError('SCIP rejected one-thread bound')
    solver.SetTimeLimit(max(1, int(max_seconds * 1000)))
    parameters = f'limits/memory = {max_memory_mb}\n'
    if not solver.SetSolverSpecificParametersAsString(parameters):
        raise RuntimeError('SCIP rejected explicit memory bound')
    nodes = {n['id']: n for n in graph['nodes']}
    edges = {e['id']: e for e in graph['edges']}
    incident, contributions = defaultdict(list), defaultdict(list)
    for e in graph['edges']:
        incident[e['u']].append((e['id'], 1))
        incident[e['v']].append((e['id'], -1))
    occupancy = {}
    for ni, net in enumerate(graph['nets']):
        sinks = len(net['terminals']) - 1
        flow = {}
        for ei, edge in enumerate(graph['edges']):
            used = solver.BoolVar(f'x_{ni}_{ei}')
            transfer = solver.NumVar(-sinks, sinks, f'f_{ni}_{ei}')
            occupancy[net['id'], edge['id']] = used
            flow[edge['id']] = transfer
            solver.Add(transfer <= sinks * used)
            solver.Add(transfer >= -sinks * used)
            if (edge['direction'] != 'via' and
                    nodes[edge['u']]['layer'] not in net['allowed_planar_layers']):
                solver.Add(used == 0)
            contributions[edge['id']].append(graph_model._edge_demand(net, edge, nodes) * used)
        private = defaultdict(list)
        for ci, component in enumerate(net.get('frozen_exterior_components', ())):
            for mi, member in enumerate(component[1:]):
                transfer = solver.NumVar(-sinks, sinks, f'exterior_{ni}_{ci}_{mi}')
                private[component[0]].append(transfer)
                private[member].append(-transfer)
        required, root = set(net['terminals']), net['terminals'][0]
        for node in graph['nodes']:
            name = node['id']
            balance = sinks if name == root else -1 if name in required else 0
            if incident[name] or private[name] or balance:
                solver.Add(sum(sign * flow[e] for e, sign in incident[name]) + sum(private[name]) == balance)
    for edge in graph['edges']:
        if edge['capacity'] is not None:
            solver.Add(sum(contributions[edge['id']]) + edge['fixed_usage'] <= edge['capacity'])
    if solver.NumVariables() != count or count > max_variables:
        raise RuntimeError('Constructed SCIP variable census differs')
    model_bytes = solver.ExportModelAsLpFormat(False).encode()
    native = solver.Solve()
    normalized = _status(native, pywraplp.Solver)
    labels = {pywraplp.Solver.OPTIMAL: 'OPTIMAL', pywraplp.Solver.FEASIBLE: 'FEASIBLE',
              pywraplp.Solver.INFEASIBLE: 'INFEASIBLE', pywraplp.Solver.NOT_SOLVED: 'NOT_SOLVED'}
    result = dict(schema_version=graph['schema_version'], status=normalized, native_status=labels[native],
        solver=dict(name='ortools-mpsolver-scip', ortools_version=ortools.__version__, native_version=version),
        graph_sha256=graph_model.digest(graph_model.canonical_bytes(graph)),
        model_sha256=graph_model.digest(model_bytes), model_hash_format='MPSolver_ExportModelAsLpFormat_false_UTF8',
        model_size=dict(nodes=len(nodes), edges=len(edges), nets=len(graph['nets']), variables=count,
                        constraints=solver.NumConstraints(), continuous_connectivity_variables=len(edges)*len(graph['nets'])+private_count,
                        binary_occupancy_variables=len(edges)*len(graph['nets'])),
        limits=dict(wall_seconds=max_seconds, solver_memory_mb=max_memory_mb, variables=max_variables,
                    workers=1, os_memory_limit_enforced=False, scip_parameters=parameters),
        wall_time_ms=solver.WallTime(), contract=graph['contract'], provenance=graph['provenance'],
        conclusion_scope='declared_explicit_graph_only', native_inputs_authenticated=False,
        physical_acceptance=False, timing_acceptance=False, infeasibility_independently_certified=False,
        witness=None, witness_sha256=None, witness_check=None)
    if normalized == 'FEASIBLE':
        witness = {}
        for net in graph['nets']:
            selected = {eid for eid in edges if _occupancy(occupancy[net['id'], eid].solution_value())}
            reached = graph_model._connected(edges, selected, net['terminals'][0], net.get('frozen_exterior_components', ()))
            witness[net['id']] = sorted(e for e in selected if edges[e]['u'] in reached)
        result['witness_check'] = graph_model.validate_witness(graph, witness)
        result['witness'] = witness
        result['witness_sha256'] = graph_model.digest(graph_model.canonical_bytes(witness))
    return result

"""Abstract graph qualification; these fixtures are NOT extracted WARP routing.

The independent exhaustive oracle below enumerates connected occupied-edge sets,
not the CP-SAT flow formulation. Optional dependency absence is the ONLY reason
to skip solver qualification; an installed incompatible/broken solver must fail.
"""
from copy import deepcopy
import importlib.util
import itertools
import json

import pytest

from autonomy import corridor_solver as c


requires_solver = pytest.mark.skipif(importlib.util.find_spec("ortools") is None,
                                    reason="optional requirements-routing.txt not installed")


def graph():
    return {
        "schema_version": 1,
        "contract": dict(c.CONTRACT, vias="forbidden", nonpreferred="explicit_edges",
                         omitted_constraints=sorted(c.REQUIRED_OMISSIONS)),
        "provenance": {"kind": "abstract_fixture", "description": "independent tiny qualification", "source_sha256": None},
        "layers": [{"id": "M1", "preferred_direction": "horizontal"}],
        "nodes": [{"id": "a", "x": 0, "y": 0, "layer": "M1"},
                  {"id": "b", "x": 1, "y": 0, "layer": "M1"},
                  {"id": "c", "x": 2, "y": 0, "layer": "M1"},
                  {"id": "d", "x": 1, "y": 1, "layer": "M1"}],
        "edges": [{"id": "ab", "u": "a", "v": "b", "direction": "horizontal", "capacity": 1, "fixed_usage": 0},
                  {"id": "bc", "u": "b", "v": "c", "direction": "horizontal", "capacity": 1, "fixed_usage": 0},
                  {"id": "bd", "u": "b", "v": "d", "direction": "vertical", "capacity": 1, "fixed_usage": 0}],
        "nets": [{"id": "n", "terminals": ["a", "c"], "boundary_terminals": ["a", "c"],
                  "track_demand_by_layer": {"M1": 1}, "via_track_demand": None, "allowed_planar_layers": ["M1"]}],
    }


def brute_feasible(g):
    """Tiny independent full edge-subset enumeration, without model helpers."""
    nodes = {n["id"]: n for n in g["nodes"]}
    choices = []
    for net in g["nets"]:
        viable = []
        for bits in itertools.product((False, True), repeat=len(g["edges"])):
            selected = [e for e, used in zip(g["edges"], bits) if used]
            reached = {net["terminals"][0]}
            while True:
                expanded = reached | {endpoint for e in selected if e["u"] in reached or e["v"] in reached
                                      for endpoint in (e["u"], e["v"])}
                # Independent set closure; no CP flow or production BFS helper.
                for component in net.get('frozen_exterior_components', []):
                    if set(component) & reached:
                        expanded.update(component)
                if expanded == reached:
                    break
                reached = expanded
            if set(net["terminals"]) <= reached:
                viable.append(bits)
        choices.append(viable)
    for assignment in itertools.product(*choices):
        feasible = True
        for index, edge in enumerate(g["edges"]):
            demand = edge["fixed_usage"]
            for net, selected in zip(g["nets"], assignment):
                if selected[index]:
                    demand += net["track_demand_by_layer"][nodes[edge["u"]]["layer"]]
            if demand > edge["capacity"]:
                feasible = False
        if feasible:
            return True
    return False


def version2(g=None):
    g=deepcopy(graph() if g is None else g)
    g['schema_version']=2
    g['contract']['boundary']=c.EXTERIOR_BOUNDARY
    g['contract']['exterior_connectivity']=c.EXTERIOR_CONTRACT
    for net in g['nets']:net['frozen_exterior_components']=[]
    return g


@requires_solver
def test_declared_frozen_connection_avoids_artificial_interior_route():
    old=graph();old['edges']=[]
    assert c.solve(old)['status']=='INFEASIBLE'
    g=version2(old);g['nets'][0]['frozen_exterior_components']=[['a','c']]
    result=c.solve(g)
    assert result['status']=='FEASIBLE' and result['witness']=={'n':[]}
    assert result['model_size']['edges']==0
    assert result['model_size']['net_private_exterior_flow_variables']==1
    assert not result['native_inputs_authenticated'] and not result['physical_acceptance']
    assert result['schema_version']==2


@requires_solver
def test_disconnected_exterior_components_still_need_real_connecting_route():
    g=version2();g['nets'][0]['terminals']=['a','b','c','d']
    g['nets'][0]['boundary_terminals']=['a','b','c','d']
    g['nets'][0]['frozen_exterior_components']=[['a','b'],['c','d']]
    g['edges']=[e for e in g['edges'] if e['id']=='bc']
    result=c.solve(g)
    assert result['status']=='FEASIBLE' and result['witness']=={'n':['bc']}
    assert result['witness_check']['edge_usage']=={'bc':1}
    with pytest.raises(c.InputError,match='disconnected'):c.validate_witness(g,{'n':[]})
    g['edges']=[]
    assert c.solve(g)['status']=='INFEASIBLE'


@requires_solver
def test_other_net_cannot_borrow_frozen_exterior_equivalence():
    g=version2();g['edges']=[]
    g['nets'][0]['frozen_exterior_components']=[['a','c']]
    other=deepcopy(g['nets'][0]);other.update(id='other',frozen_exterior_components=[])
    g['nets'].append(other)
    assert c.solve(g)['status']=='INFEASIBLE'
    with pytest.raises(c.InputError,match='other.*disconnected'):c.validate_witness(g,{'n':[],'other':[]})


@requires_solver
@pytest.mark.parametrize('capacity,expected',[(1,'INFEASIBLE'),(2,'FEASIBLE')])
def test_private_relations_do_not_waive_physical_shared_capacity(capacity,expected):
    g=version2();g['nets'][0].update(terminals=['a','b','c','d'],boundary_terminals=['a','b','c','d'],
                                   frozen_exterior_components=[['a','b'],['c','d']])
    other=deepcopy(g['nets'][0]);other.update(id='other',terminals=['b','c'],boundary_terminals=['b','c'],frozen_exterior_components=[])
    g['nets'].append(other);g['edges']=[dict(e,capacity=capacity) for e in g['edges'] if e['id']=='bc']
    assert c.solve(g)['status']==expected
    if capacity==1:
        with pytest.raises(c.InputError,match='capacity exceeded'):c.validate_witness(g,{'n':['bc'],'other':['bc']})


@pytest.mark.parametrize('components',[[['a']],[['a','a']],[['a','c'],['a','d']],[['a','b']],[['a','unknown']],['a']])
def test_bad_exterior_components_rejected(components):
    g=version2();g['nets'][0]['frozen_exterior_components']=components
    with pytest.raises(c.InputError):c.validate_graph(g)


def test_exterior_schema_and_contract_are_explicit_no_v1_relaxation():
    g=graph();g['nets'][0]['frozen_exterior_components']=[['a','c']]
    with pytest.raises(c.InputError):c.validate_graph(g)
    g=version2();g['contract']['boundary']=c.CONTRACT['boundary']
    with pytest.raises(c.InputError):c.validate_graph(g)
    g=version2();g['contract'].pop('exterior_connectivity')
    with pytest.raises(c.InputError):c.validate_graph(g)


def test_exterior_links_count_towards_existing_variable_limit():
    g=version2();g['edges']=[];g['nets'][0]['terminals']=['a','c','d'];g['nets'][0]['boundary_terminals']=['a','c','d']
    g['nets'][0]['frozen_exterior_components']=[['a','c','d']]
    with pytest.raises(c.InputError,match='requires 2 variables'):c.solve(g,max_variables=1)


def test_exterior_component_and_global_link_limits(monkeypatch):
    g=version2();g['nets'][0]['frozen_exterior_components']=[['a','c']]
    monkeypatch.setattr(c,'MAX_EXTERIOR_LINKS',0)
    with pytest.raises(c.InputError,match='virtual-link limit'):c.validate_graph(g)
    monkeypatch.setattr(c,'MAX_EXTERIOR_LINKS',12000)
    g['nets'][0]['frozen_exterior_components']=[['a','c']]*(c.MAX_NODES//2+1)
    with pytest.raises(c.InputError,match='list of size'):c.validate_graph(g)


@requires_solver
def test_exterior_component_order_is_canonical_without_changing_layer_order():
    g=version2();g['nets'][0].update(terminals=['a','b','c','d'],boundary_terminals=['a','b','c','d'],
                                   frozen_exterior_components=[['a','b'],['c','d']])
    before=deepcopy(g);first=c.solve(g)
    assert g==before
    g['nets'][0]['frozen_exterior_components']=[['d','c'],['b','a']]
    second=c.solve(g)
    assert first['graph_sha256']==second['graph_sha256'] and first['model_sha256']==second['model_sha256']


@requires_solver
@pytest.mark.parametrize('capacities',list(itertools.product(range(3),repeat=3)))
@pytest.mark.parametrize('component',[[],[['a','c']],[['c','d']]])
def test_private_exterior_matches_independent_exhaustive_subsets(capacities,component):
    g=version2();g['nets'][0].update(terminals=['a','c','d'],boundary_terminals=['a','c','d'],frozen_exterior_components=component)
    other=deepcopy(g['nets'][0]);other.update(id='other',terminals=['c','d'],boundary_terminals=['c','d'],frozen_exterior_components=[])
    g['nets'].append(other)
    for edge,capacity in zip(g['edges'],capacities):edge['capacity']=capacity
    expected='FEASIBLE' if brute_feasible(g) else 'INFEASIBLE'
    assert c.solve(g)['status']==expected


def test_validate_copies_and_canonicalizes_without_mutating():
    g = graph()
    before = deepcopy(g)
    g["nodes"].reverse()
    canonical = c.validate_graph(g)
    assert canonical["nodes"] == before["nodes"]
    assert g["nodes"] == list(reversed(before["nodes"]))
    canonical["nets"][0]["terminals"].append("b")
    assert g["nets"][0]["terminals"] == ["a", "c"]


def test_shared_trunk_charged_once_for_multiple_sinks():
    g = graph()
    g["nets"][0]["terminals"] = ["a", "c", "d"]
    checked = c.validate_witness(g, {"n": ["ab", "bc", "bd"]})
    assert checked["edge_usage"] == {"ab": 1, "bc": 1, "bd": 1}
    assert checked["terminal_connectivity"] and not checked["physical_acceptance"]


def test_direction_is_geometric_and_undirected_traversal_shares_resource():
    g = graph()
    g["edges"][0]["u"], g["edges"][0]["v"] = "b", "a"
    assert c.validate_witness(g, {"n": ["ab", "bc"]})["checked"]


@pytest.mark.parametrize("mutate", [
    lambda g: g.update(unexpected=True),
    lambda g: g.pop("contract"),
    lambda g: g.update(schema_version=True),
    lambda g: g["contract"].update(occupancy="per_sink_flow"),
    lambda g: g["contract"].update(fixed_usage="includes_selected_nets"),
    lambda g: g["contract"].update(terminals="some_terminal_may_disappear"),
    lambda g: g["contract"].update(boundary="implicit_outside_connection"),
    lambda g: g["contract"].update(omitted_constraints=[]),
    lambda g: g["contract"].update(omitted_constraints=["physical_drc"] * 4),
    lambda g: g["contract"].update(vias="assumed_physical"),
    lambda g: g["contract"].update(nonpreferred="assumed"),
    lambda g: g["provenance"].update(kind="authenticated_openroad"),
    lambda g: g["provenance"].update(kind="external_explicit_graph"),
    lambda g: g["provenance"].update(source_sha256="z" * 64),
    lambda g: g["layers"].append(deepcopy(g["layers"][0])),
    lambda g: g["layers"][0].update(preferred_direction="diagonal"),
    lambda g: g["nodes"].append(deepcopy(g["nodes"][0])),
    lambda g: g["nodes"][0].update(x=True),
    lambda g: g["nodes"][0].update(layer=[]),
    lambda g: g["nodes"][0].update(id="bad\nname"),
    lambda g: g["nodes"][1].update(x=0),
    lambda g: g["edges"].append(dict(g["edges"][0], id="duplicate-pair")),
    lambda g: g["edges"][0].update(capacity=True),
    lambda g: g["edges"][0].update(capacity=1.0),
    lambda g: g["edges"][0].update(capacity=-1),
    lambda g: g["edges"][0].update(capacity=None),
    lambda g: g["edges"][0].update(fixed_usage=-1),
    lambda g: g["edges"][0].update(u=[]),
    lambda g: g["edges"][0].update(v="missing"),
    lambda g: g["edges"][0].update(v="a"),
    lambda g: g["edges"][0].update(direction="vertical"),
    lambda g: g["edges"][0].update(direction="via"),
    lambda g: g["edges"][0].update(v="d"),
    lambda g: g["contract"].update(nonpreferred="forbidden"),
    lambda g: g["nets"].append(deepcopy(g["nets"][0])),
    lambda g: g["nets"][0].update(terminals=[]),
    lambda g: g["nets"][0].update(terminals=["a", "a"]),
    lambda g: g["nets"][0].update(terminals=["a", "missing"]),
    lambda g: g["nets"][0].update(boundary_terminals=["b"]),
    lambda g: g["nets"][0].update(track_demand_by_layer={}),
    lambda g: g["nets"][0].update(track_demand_by_layer={"M1": 0}),
    lambda g: g["nets"][0].update(track_demand_by_layer={"M1": 1, "M2": 1}),
    lambda g: g["nets"][0].update(via_track_demand=0),
    lambda g: g["nets"][0].update(allowed_planar_layers=[]),
    lambda g: g["nets"][0].update(allowed_planar_layers=["M2"]),
])
def test_malformed_inputs_fail_closed(mutate):
    g = graph()
    mutate(g)
    with pytest.raises(c.InputError):
        c.validate_graph(g)


@pytest.mark.parametrize("witness", [{}, {"n": []}, {"n": ["ab"]}, {"n": ["ab", "bc", "bc"]},
                                     {"n": ["ab", "missing"]}, {"n": ["ab", "bc"], "other": []}])
def test_bad_witnesses_fail_closed(witness):
    with pytest.raises(c.InputError):
        c.validate_witness(graph(), witness)


def test_witness_rejects_fixed_usage_and_weighted_demand_overflow():
    g = graph()
    g["nets"][0]["track_demand_by_layer"]["M1"] = 2
    with pytest.raises(c.InputError, match="capacity exceeded"):
        c.validate_witness(g, {"n": ["ab", "bc"]})
    g["nets"][0]["track_demand_by_layer"]["M1"] = 1
    g["edges"][0]["fixed_usage"] = 1
    with pytest.raises(c.InputError, match="capacity exceeded"):
        c.validate_witness(g, {"n": ["ab", "bc"]})


def test_witness_rejects_disconnected_extraneous_occupancy():
    g = graph()
    g["nodes"].extend([{"id": "p", "x": 10, "y": 0, "layer": "M1"},
                       {"id": "q", "x": 11, "y": 0, "layer": "M1"}])
    g["edges"].append({"id": "pq", "u": "p", "v": "q", "direction": "horizontal", "capacity": 1, "fixed_usage": 0})
    with pytest.raises(c.InputError, match="extraneous"):
        c.validate_witness(g, {"n": ["ab", "bc", "pq"]})


def test_duplicate_json_keys_and_nonfinite_numbers_rejected(tmp_path):
    path = tmp_path / "bad.json"
    for text in ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}', 'not json']:
        path.write_text(text)
        with pytest.raises(c.InputError):
            c.load_graph(path)


def test_graph_load_records_exact_raw_bytes(tmp_path):
    path = tmp_path / "graph.json"
    raw = json.dumps(graph(), indent=2).encode()
    path.write_bytes(raw)
    validated, fingerprint = c.load_graph(path)
    assert fingerprint == c.digest(raw)
    assert validated == c.validate_graph(graph())


def test_model_size_limit_rejects_before_optional_import():
    with pytest.raises(c.InputError, match="exceeds declared limit"):
        c.solve(graph(), max_variables=1)


@pytest.mark.parametrize("options", [{"max_seconds": 0}, {"max_seconds": float("nan")},
                                      {"max_seconds": True}, {"max_seconds": 301},
                                      {"max_deterministic_time": 0}, {"max_memory_mb": 0},
                                      {"max_memory_mb": 4097}, {"max_variables": 0}])
def test_bad_solver_limits_fail_before_optional_import(options):
    with pytest.raises(c.InputError):
        c.solve(graph(), **options)


@requires_solver
def test_cp_sat_feasible_and_witness_independently_checked():
    g = graph()
    result = c.solve(g)
    assert result["status"] == "FEASIBLE"
    assert result["native_status"] in ("OPTIMAL", "FEASIBLE")
    assert result["solver"]["version"] == c.SOLVER_VERSION
    assert result["witness_check"] == c.validate_witness(g, result["witness"])
    assert not result["native_inputs_authenticated"] and not result["physical_acceptance"]
    assert result["conclusion_scope"] == "declared_explicit_graph_only"
    assert len(result["model_sha256"]) == 64
    assert result["model_size"]["variables"] <= result["limits"]["variables"]


@requires_solver
def test_cp_sat_shared_multisink_trunk_uses_one_track():
    g = graph()
    g["nets"][0]["terminals"] = ["a", "c", "d"]
    result = c.solve(g)
    assert result["status"] == "FEASIBLE"
    assert result["witness_check"]["edge_usage"] == {"ab": 1, "bc": 1, "bd": 1}


@requires_solver
def test_cp_sat_joint_topology_choice_uses_two_disjoint_paths():
    g = graph()
    g["nodes"] = [{"id": name, "x": x, "y": y, "layer": "M1"}
                  for name, x, y in [("a", 0, 0), ("b", 1, 0), ("c", 2, 0),
                                     ("d", 0, 1), ("e", 1, 1), ("f", 2, 1)]]
    g["edges"] = [{"id": u + v, "u": u, "v": v, "direction": direction, "capacity": 1, "fixed_usage": 0}
                  for u, v, direction in [("a", "b", "horizontal"), ("b", "c", "horizontal"),
                                          ("d", "e", "horizontal"), ("e", "f", "horizontal"),
                                          ("a", "d", "vertical"), ("b", "e", "vertical"), ("c", "f", "vertical")]]
    g["nets"].append(dict(deepcopy(g["nets"][0]), id="second"))
    assert brute_feasible(g)
    result = c.solve(g)
    assert result["status"] == "FEASIBLE"
    assert not set(result["witness"]["n"]) & set(result["witness"]["second"])
    assert c.validate_witness(g, result["witness"])["checked"]


@requires_solver
@pytest.mark.parametrize("capacity,expected", [(1, "INFEASIBLE"), (2, "FEASIBLE")])
def test_cp_sat_separate_nets_share_capacity_only_when_available(capacity, expected):
    g = graph()
    g["nets"].append(dict(deepcopy(g["nets"][0]), id="second"))
    for edge in g["edges"]:
        edge["capacity"] = capacity
    result = c.solve(g)
    assert result["status"] == expected
    if expected == "INFEASIBLE":
        assert result["witness"] is None
        assert result["witness_check"] is None
        assert not result["infeasibility_independently_certified"]


@requires_solver
@pytest.mark.parametrize("case", ["disconnected", "fixed_full", "fixed_overfull", "weighted"])
def test_cp_sat_rejects_disconnected_boundary_and_residual_capacity(case):
    g = graph()
    if case == "disconnected":
        g["edges"] = g["edges"][1:]
    elif case == "weighted":
        g["nets"][0]["track_demand_by_layer"]["M1"] = 2
    else:
        g["edges"][0]["fixed_usage"] = 1 if case == "fixed_full" else 2
    result = c.solve(g)
    assert result["status"] == "INFEASIBLE" and result["witness"] is None


def multilayer():
    g = graph()
    g["contract"]["vias"] = "unlimited_coarse_edges"
    g["layers"].append({"id": "M2", "preferred_direction": "horizontal"})
    g["nodes"].extend([{"id": "a2", "x": 0, "y": 0, "layer": "M2"},
                       {"id": "c2", "x": 2, "y": 0, "layer": "M2"}])
    g["edges"] = [{"id": "va", "u": "a", "v": "a2", "direction": "via", "capacity": None, "fixed_usage": 0},
                  {"id": "vc", "u": "c2", "v": "c", "direction": "via", "capacity": None, "fixed_usage": 0},
                  {"id": "ac2", "u": "a2", "v": "c2", "direction": "horizontal", "capacity": 2, "fixed_usage": 0}]
    g["nets"][0].update(track_demand_by_layer={"M1": 1, "M2": 2},
                         via_track_demand=0, allowed_planar_layers=["M1", "M2"])
    return g


@requires_solver
def test_cp_sat_explicit_vias_and_layer_specific_costs():
    g = multilayer()
    result = c.solve(g)
    assert result["status"] == "FEASIBLE"
    assert result["witness_check"]["edge_usage"] == {"va": 0, "vc": 0, "ac2": 2}
    g["nets"][0]["track_demand_by_layer"]["M2"] = 3
    assert c.solve(g)["status"] == "INFEASIBLE"


@requires_solver
def test_cp_sat_planar_limits_do_not_remove_via_only_access():
    g = multilayer()
    g["nets"][0]["allowed_planar_layers"] = ["M1"]
    assert c.solve(g)["status"] == "INFEASIBLE"
    # A pin on an otherwise planar-forbidden layer can still use a declared via.
    g["nets"][0]["terminals"] = ["a", "a2"]
    g["nets"][0]["boundary_terminals"] = []
    assert c.solve(g)["status"] == "FEASIBLE"


def test_independent_witness_check_rejects_planar_forbidden_layer():
    g = multilayer()
    g["nets"][0]["allowed_planar_layers"] = ["M1"]
    with pytest.raises(c.InputError, match="forbidden planar layer"):
        c.validate_witness(g, {"n": ["va", "ac2", "vc"]})


@requires_solver
def test_cp_sat_explicit_via_capacity_is_not_implicitly_unlimited():
    g = multilayer()
    g["contract"]["vias"] = "explicit_capacity_edges"
    g["nets"][0]["via_track_demand"] = 2
    for edge in g["edges"][:2]:
        edge["capacity"] = 1
    assert c.solve(g)["status"] == "INFEASIBLE"


@pytest.mark.parametrize("mutate", [
    lambda g: g["edges"][0].update(capacity=0),
    lambda g: g["edges"][0].update(fixed_usage=1),
    lambda g: g["edges"][0].update(v="c2"),
    lambda g: g["nets"][0].update(via_track_demand=1),
    lambda g: g["layers"].insert(1, {"id": "MID", "preferred_direction": "vertical"}),
])
def test_via_assumptions_require_exact_explicit_contract(mutate):
    g = multilayer()
    mutate(g)
    with pytest.raises(c.InputError):
        c.validate_graph(g)


@requires_solver
@pytest.mark.parametrize("terminals,expected", [(["a"], "FEASIBLE"), (["a", "c"], "INFEASIBLE")])
def test_cp_sat_no_edges_has_honest_connectivity_status(terminals, expected):
    g = graph()
    g["edges"] = []
    g["nets"][0]["terminals"] = terminals
    g["nets"][0]["boundary_terminals"] = []
    assert c.solve(g)["status"] == expected


@requires_solver
def test_cp_sat_timeout_is_unknown_without_a_witness():
    result = c.solve(graph(), max_seconds=1e-12)
    assert result["status"] == "UNKNOWN"
    assert result["native_status"] == "UNKNOWN"
    assert result["witness"] is None and result["witness_check"] is None


@requires_solver
def test_equivalent_input_order_retains_graph_and_model_hashes():
    g = graph()
    first = c.solve(g)
    g["nodes"].reverse()
    g["edges"].reverse()
    g["nets"][0]["terminals"].reverse()
    second = c.solve(g)
    assert first["graph_sha256"] == second["graph_sha256"]
    assert first["model_sha256"] == second["model_sha256"]


@requires_solver
@pytest.mark.parametrize("capacities", list(itertools.product(range(3), repeat=3)))
def test_cp_sat_matches_independent_exhaustive_multinet_oracle(capacities):
    g = graph()
    g["nets"][0]["terminals"] = ["a", "c", "d"]
    g["nets"][0]["boundary_terminals"] = []
    g["nets"].append(dict(deepcopy(g["nets"][0]), id="other", terminals=["c", "d"]))
    for edge, capacity in zip(g["edges"], capacities):
        edge["capacity"] = capacity
    independently_feasible = brute_feasible(g)
    result = c.solve(g)
    assert result["status"] == ("FEASIBLE" if independently_feasible else "INFEASIBLE")


@requires_solver
def test_cli_retains_raw_input_hash_and_model_scope(tmp_path):
    source = tmp_path / "explicit.json"
    output = tmp_path / "result.json"
    source.write_text(json.dumps(graph()))
    assert c.main([str(source), "--output", str(output)]) == 0
    result = json.loads(output.read_text())
    assert result["input_file_sha256"] == c.digest(source.read_bytes())
    assert result["status"] == "FEASIBLE" and not result["physical_acceptance"]
    assert result["witness_check"]["checked"]

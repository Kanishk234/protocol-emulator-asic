"""Independent arithmetic certificate for an axis cut in a declared graph.

No solver is invoked. Net-private exterior connections crossing the partition
make this conservative checker refuse certification. Scope never exceeds input.
"""
from autonomy import corridor_solver as model


def certify(graph, *, axis, coordinate):
    graph=model.validate_graph(graph)
    if axis not in ('x','y') or type(coordinate) is not int:
        raise ValueError('Require x/y axis and integer cut coordinate')
    nodes={n['id']:n for n in graph['nodes']}
    side=lambda node:nodes[node][axis]<=coordinate
    for net in graph['nets']:
        if any(len({side(n) for n in component})>1 for component in net.get('frozen_exterior_components',())):
            raise ValueError('Private exterior connectivity crosses this cut; certificate unsupported')
    edges=[]
    for edge in graph['edges']:
        if side(edge['u'])!=side(edge['v']):
            if edge['capacity'] is None:
                raise ValueError('Unbounded physical resource crosses cut')
            remaining=edge['capacity']-edge['fixed_usage']
            if remaining<0:
                raise ValueError('Fixed resource violation requires separate certificate')
            edges.append(dict(id=edge['id'],capacity=edge['capacity'],fixed_usage=edge['fixed_usage'],residual=remaining))
    required=[]
    for net in graph['nets']:
        if len({side(n) for n in net['terminals']})>1:
            # Minimum over ALL declared layers is a safe lower bound, including
            # unavailable layers. It can weaken the certificate, never strengthen it.
            required.append(dict(net=net['id'],minimum_crossing_demand=min(net['track_demand_by_layer'].values())))
    capacity=sum(e['residual'] for e in edges)
    demand=sum(n['minimum_crossing_demand'] for n in required)
    return dict(schema_version=1,axis=axis,coordinate=coordinate,
        graph_sha256=model.digest(model.canonical_bytes(graph)),
        residual_crossing_capacity=capacity,required_crossing_demand_lower_bound=demand,
        independently_verified_graph_infeasible=demand>capacity,
        crossing_edges=edges,required_nets=required,
        native_inputs_authenticated=False,physical_acceptance=False,timing_acceptance=False,
        scope='Arithmetic cut inequality for the supplied graph only; no whole-chip or physical impossibility')


def certify_partition(graph, *, side_nodes):
    """Check an explicit partition without trusting how it was discovered."""
    graph=model.validate_graph(graph)
    if not isinstance(side_nodes,list) or not side_nodes or any(not isinstance(n,str) for n in side_nodes):
        raise ValueError('Require nonempty explicit node list')
    side=set(side_nodes);all_nodes={n['id'] for n in graph['nodes']}
    if len(side)!=len(side_nodes) or not side<all_nodes:
        raise ValueError('Partition must be unique known nodes and proper subset')
    for net in graph['nets']:
        if any(len({n in side for n in component})>1 for component in net.get('frozen_exterior_components',())):
            raise ValueError('Private exterior connectivity crosses partition')
    edges=[]
    for edge in graph['edges']:
        if (edge['u'] in side)!=(edge['v'] in side):
            if edge['direction']=='via':
                raise ValueError('Via-crossing partitions require a separate demand bound')
            if edge['capacity'] is None or edge['capacity']<edge['fixed_usage']:
                raise ValueError('Crossing resource must have finite nonnegative residual')
            edges.append(dict(id=edge['id'],capacity=edge['capacity'],fixed_usage=edge['fixed_usage'],
                residual=edge['capacity']-edge['fixed_usage']))
    required=[dict(net=n['id'],minimum_crossing_demand=min(n['track_demand_by_layer'].values()))
        for n in graph['nets'] if len({t in side for t in n['terminals']})>1]
    capacity=sum(e['residual'] for e in edges);demand=sum(n['minimum_crossing_demand'] for n in required)
    return dict(schema_version=1,side_nodes=sorted(side),
        graph_sha256=model.digest(model.canonical_bytes(graph)),
        residual_crossing_capacity=capacity,required_crossing_demand_lower_bound=demand,
        independently_verified_graph_infeasible=demand>capacity,crossing_edges=edges,required_nets=required,
        native_inputs_authenticated=False,physical_acceptance=False,timing_acceptance=False,
        scope='Arithmetic explicit-partition inequality for supplied graph only; no whole-chip or physical impossibility')


def discover_partition_certificate(graph, *, max_pairs=128):
    """Propose terminal-pair mincuts, certify each arithmetically, return strongest.

    Discovery supports only finite-capacity single-layer unit-demand v1 graphs.
    Failure to find a deficit is inconclusive; pair cuts are not complete.
    """
    graph=model.validate_graph(graph)
    if (graph['schema_version']!=1 or len(graph['layers'])!=1 or
            any(e['capacity'] is None or e['capacity']<e['fixed_usage'] for e in graph['edges']) or
            any(list(n['track_demand_by_layer'].values())!=[1] for n in graph['nets'])):
        raise ValueError('Discovery requires finite nonnegative single-layer unit-demand graph')
    if type(max_pairs) is not int or not 1<=max_pairs<=128:
        raise ValueError('Discovery pair bound must be 1..128')
    pairs=[(n['terminals'][0],t) for n in graph['nets'] for t in n['terminals'][1:]]
    if len(pairs)>max_pairs:raise ValueError('Terminal-pair discovery exceeds bound')
    from ortools.graph.python import max_flow
    ids={n['id']:i for i,n in enumerate(graph['nodes'])};best=None;best_deficit=0
    for root,sink in pairs:
        flow=max_flow.SimpleMaxFlow()
        for e in graph['edges']:
            residual=e['capacity']-e['fixed_usage']
            flow.add_arc_with_capacity(ids[e['u']],ids[e['v']],residual)
            flow.add_arc_with_capacity(ids[e['v']],ids[e['u']],residual)
        if flow.solve(ids[root],ids[sink])!=flow.OPTIMAL:
            raise ValueError('Mincut discovery did not complete')
        side=[graph['nodes'][i]['id'] for i in flow.get_source_side_min_cut()]
        certificate=certify_partition(graph,side_nodes=side)
        deficit=certificate['required_crossing_demand_lower_bound']-certificate['residual_crossing_capacity']
        if deficit>best_deficit:best,best_deficit=certificate,deficit
    return best

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

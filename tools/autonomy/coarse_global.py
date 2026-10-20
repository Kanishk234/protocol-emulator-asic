"""Global unit-demand routing under explicitly unlimited coarse vias.

Only all-layer, unit-demand cohorts qualify. Parallel native planar residual
capacities then combine exactly for this relaxation; a witness is allocated
back to original layers and its per-net layer connectivity is checked.
Unrelated fixed overflow is retained, never inflated into available capacity.
"""
from collections import Counter,defaultdict,deque
import hashlib
import json
from pathlib import Path

from autonomy import corridor_solver as solver,native_corridor as raw,native_terminals as terminals


class ModelError(ValueError):
    pass


def _state(snapshot,state,slots):
    admission=terminals.audit_selection(snapshot,state,slots)
    if not admission['selected_membership_and_access_verified']:
        raise ModelError('Selected terminal membership/access unsupported')
    nl=snapshot.grid[2]
    fixed={edge:data[1] for edge,data in snapshot.edges.items()}
    for slot in slots:
        net=snapshot.nets[slot]
        if net['minimum_layer']!=0 or net['maximum_layer']!=nl-1 or net['demands']!=[1]*nl:
            raise ModelError('Layer aggregation requires unit demand and every native planar layer')
        for edge,count in net['planar_step_multiplicity'].items():fixed[edge]-=count
    if any(value<0 for value in fixed.values()):raise ModelError('Exact old multiset release exceeds raw usage')
    return admission,fixed


def _endpoints(edge):
    direction,x,y=edge
    return (x,y),(x+(direction=='H'),y+(direction=='V'))


def _name(point):return 'p%d_%d'%point


def build(snapshot,state,*,slots):
    admission,fixed=_state(snapshot,state,slots)
    capacities=Counter()
    for (direction,layer,x,y),data in snapshot.edges.items():
        # Existing fixed violations have zero available demand, never a credit.
        capacities[direction,x,y]+=max(0,data[0]-fixed[direction,layer,x,y])
    adjacent=defaultdict(set)
    for edge,capacity in capacities.items():
        if capacity:
            a,b=_endpoints(edge);adjacent[a].add(b);adjacent[b].add(a)
    pins={pin[:2] for slot in slots for pin in snapshot.nets[slot]['pins']}
    # Components with no selected terminal cannot help connect any required net.
    reached=set(pins);queue=deque(pins)
    while queue:
        for point in adjacent[queue.popleft()]-reached:reached.add(point);queue.append(point)
    edges=[dict(id='%s_%d_%d'%edge,u=_name(_endpoints(edge)[0]),v=_name(_endpoints(edge)[1]),
                direction='horizontal' if edge[0]=='H' else 'vertical',capacity=capacity,fixed_usage=0)
           for edge,capacity in sorted(capacities.items()) if capacity and set(_endpoints(edge))<=reached]
    if len(reached)>solver.MAX_NODES or len(edges)>solver.MAX_EDGES or 2*len(edges)*len(slots)>solver.MAX_VARIABLES:
        raise ModelError('Aggregated component exceeds configured model bounds')
    provenance=dict(raw_sha256=snapshot.sha256,terminal_sha256=state.sha256,slots=sorted(slots),
        generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        premise='all_native_layers_available_unit_demand_unlimited_coarse_vias')
    source=hashlib.sha256(json.dumps(provenance,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    graph=solver.validate_graph(dict(schema_version=1,
        contract=dict(solver.CONTRACT,vias='forbidden',nonpreferred='explicit_edges',
            omitted_constraints=sorted(solver.REQUIRED_OMISSIONS|{'native_via_feasibility','native_layer_identity_collapsed_under_unlimited_vias','fixed_background_overflow_retained'})),
        provenance=dict(kind='external_explicit_graph',description='Unit/all-layer native cohort aggregated under unlimited coarse vias; fixed old overflow retained separately',source_sha256=source),
        layers=[dict(id='aggregate',preferred_direction='horizontal')],
        nodes=[dict(id=_name(p),x=p[0],y=p[1],layer='aggregate') for p in sorted(reached)],edges=edges,
        nets=[dict(id=str(slot),terminals=sorted({_name(p[:2]) for p in snapshot.nets[slot]['pins']}),
            boundary_terminals=[],track_demand_by_layer={'aggregate':1},via_track_demand=None,
            allowed_planar_layers=['aggregate']) for slot in sorted(slots)]))
    baseline_overflow=sum(max(0,fixed[e]-v[0]) for e,v in snapshot.edges.items())
    return dict(graph=graph,provenance=provenance,admission=admission,
        fixed_background_overflow=baseline_overflow,model_variables=2*len(edges)*len(slots),
        native_inputs_authenticated=False,physical_acceptance=False,timing_acceptance=False,
        scope='Global selected-cohort coarse relaxation only; other routes fixed, original capacities, unlimited coarse vias')


def allocate_and_check(snapshot,state,model,witness):
    """Check a model witness, restore original-layer charges and pin connectivity."""
    slots=model['provenance']['slots']
    rebuilt=build(snapshot,state,slots=slots)
    if rebuilt!=model:raise ModelError('Model differs from independently reconstructed native inputs')
    solver.validate_witness(model['graph'],witness)
    _,fixed=_state(snapshot,state,slots)
    nl=snapshot.grid[2]
    edges={e['id']:e for e in model['graph']['edges']}
    nodes={n['id']:n for n in model['graph']['nodes']}
    used=defaultdict(list)
    for slot in slots:
        for edge in witness[str(slot)]:used[edge].append(slot)
    assignments={slot:[] for slot in slots}
    proposed=dict(fixed)
    for eid,owners in sorted(used.items()):
        edge=edges[eid];u,v=nodes[edge['u']],nodes[edge['v']]
        direction='H' if u['y']==v['y'] else 'V'
        x,y=min(u['x'],v['x']),min(u['y'],v['y'])
        available={layer:max(0,snapshot.edges[direction,layer,x,y][0]-fixed[direction,layer,x,y]) for layer in range(nl)}
        for slot in sorted(owners):
            layer=next((l for l in range(nl) if available[l]),None)
            if layer is None:raise ModelError('Aggregated witness cannot be assigned to original layer capacities')
            available[layer]-=1
            resource=(direction,layer,x,y);proposed[resource]+=1;assignments[slot].append(resource)
    routes={}
    for slot in slots:
        planar=assignments[slot];at=defaultdict(set);links=set()
        for d,l,x,y in planar:
            a=(x,y,l);b=(x+(d=='H'),y+(d=='V'),l)
            links.add(tuple(sorted((a,b))));at[a[:2]].add(l);at[b[:2]].add(l)
        for x,y,l in snapshot.nets[slot]['pins']:at[x,y].add(l)
        vias=[]
        for (x,y),layers in sorted(at.items()):
            for layer in range(min(layers),max(layers)):
                links.add(((x,y,layer),(x,y,layer+1)));vias.append((x,y,layer,layer+1))
        adjacent=defaultdict(set)
        for a,b in links:adjacent[a].add(b);adjacent[b].add(a)
        pins=set(snapshot.nets[slot]['pins']);reached={min(pins)};queue=deque(reached)
        while queue:
            for point in adjacent[queue.popleft()]-reached:reached.add(point);queue.append(point)
        if not pins<=reached or any(a not in reached or b not in reached for a,b in links):
            raise ModelError('Allocated layer/via route fails native pin connectivity')
        routes[str(slot)]=dict(name=snapshot.nets[slot]['name'],planar_resources=planar,unlimited_coarse_vias=vias)
    if any(proposed[e]>max(v[0],fixed[e]) for e,v in snapshot.edges.items()):
        raise ModelError('Witness adds overflow beyond unchanged fixed background')
    old=sum(max(0,v[1]-v[0]) for v in snapshot.edges.values())
    new=sum(max(0,proposed[e]-v[0]) for e,v in snapshot.edges.items())
    return dict(original_raw_overflow=old,fixed_background_overflow=model['fixed_background_overflow'],
        proposed_raw_overflow=new,original_layer_capacity_allocation_checked=True,
        native_pin_connectivity_under_unlimited_vias_checked=True,routes=routes,
        native_inputs_authenticated=False,physical_acceptance=False,timing_acceptance=False,
        scope='Constructive coarse-via witness only; no native route installation, guide handoff or physical/timing signoff')

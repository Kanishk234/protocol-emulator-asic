"""Bounded WARP-derived coarse graph extraction; never a physical routing claim.

Keep exact old STEP multiplicities for release, published native segments for
frozen connectivity, and explicit unlimited coarse vias as a declared relaxation.
The caller separately authenticates workflow/patch/checkpoint provenance.
"""
from collections import Counter, defaultdict, deque
import hashlib
import json
from pathlib import Path

from autonomy import corridor_solver as solver
from autonomy import native_corridor as raw
from autonomy import native_terminals as terminals


class ExtractionError(ValueError):
    pass


def _link(a, b):
    return tuple(sorted((a, b)))


def _components(edges):
    adjacent = defaultdict(set)
    for a, b in edges:
        adjacent[a].add(b)
        adjacent[b].add(a)
    components = []
    pending = set(adjacent)
    while pending:
        root = min(pending)
        reached, queue = {root}, deque([root])
        while queue:
            for node in adjacent[queue.popleft()]-reached:
                reached.add(node)
                queue.append(node)
        pending -= reached
        components.append(reached)
    return components


def _read_segments(text, snapshot, state, selected):
    """Preserve exact raw names, expand selected DBU segments without rounding."""
    if not isinstance(text, str) or len(text.encode()) > raw.MAX_BYTES:
        raise ExtractionError('Published segment input exceeds limit')
    nx, ny, nl, ox, oy, pitch = snapshot.grid
    if pitch % 2:
        raise ExtractionError('Odd grid pitch has no supported integer center contract')
    names = {n['name']: slot for slot, n in snapshot.nets.items()}
    layers = {v['name']: v['index'] for v in state.layers}
    lines = text.splitlines()
    if len(lines) > raw.MAX_ROWS:
        raise ExtractionError('Published segment row limit exceeded')
    index, seen, result = 0, set(), {}
    while index < len(lines):
        name = lines[index]
        if name not in names or name in seen or index+1 >= len(lines) or lines[index+1] != '(':
            raise ExtractionError('Published net name/order/inventory mismatch')
        seen.add(name)
        index += 2
        links, count = set(), 0
        while index < len(lines) and lines[index] != ')':
            row = lines[index].split()
            if len(row) != 6 or row[2] not in layers or row[5] not in layers:
                raise ExtractionError('Malformed published segment')
            try:
                x0,y0,x1,y1 = (int(row[i]) for i in (0,1,3,4))
            except ValueError as exc:
                raise ExtractionError('Malformed published coordinate') from exc
            l0,l1 = layers[row[2]],layers[row[5]]
            if (x0 != x1 and y0 != y1) or (l0 != l1 and (x0 != x1 or y0 != y1)):
                raise ExtractionError('Non-Manhattan published segment')
            if names[name] in selected:
                points = []
                for x,y,l in ((x0,y0,l0),(x1,y1,l1)):
                    dx,dy = x-ox-pitch//2,y-oy-pitch//2
                    if dx % pitch or dy % pitch:
                        raise ExtractionError('Published endpoint is off native grid center')
                    point = (dx//pitch,dy//pitch,l)
                    if not (0 <= point[0] < nx and 0 <= point[1] < ny and 0 <= l < nl):
                        raise ExtractionError('Published endpoint outside native grid')
                    points.append(point)
                a,b = points
                distance = sum(abs(a[i]-b[i]) for i in range(3))
                if distance > nx+ny+nl:
                    raise ExtractionError('Published segment expansion exceeds bound')
                if not distance:
                    raise ExtractionError('Zero-length selected published segment')
                direction = tuple((b[i]>a[i])-(b[i]<a[i]) for i in range(3))
                for _ in range(distance):
                    nxt = tuple(a[i]+direction[i] for i in range(3))
                    links.add(_link(a,nxt))
                    a = nxt
            count += 1
            index += 1
        if index >= len(lines) or not count:
            raise ExtractionError('Incomplete or empty published route')
        if names[name] in selected:
            result[names[name]] = links
        index += 1
    if seen != set(names):
        raise ExtractionError('Published route inventory incomplete')
    return result


def _native_link(edge):
    direction,layer,x,y = edge
    return _link((x,y,layer),(x+(direction=='H'),y+(direction=='V'),layer))


def extract(snapshot, state, segment_text, *, slots, window):
    """Return graph + admission/release manifest, with all native scope false.

    `window` is inclusive [min_x,min_y,max_x,max_y]. Every selected net's
    published route must connect every native pin; outside connections are
    frozen, private to that net, and never converted to shared resources.
    """
    admission = terminals.audit_selection(snapshot,state,slots)
    if not admission['selected_membership_and_access_verified']:
        raise ExtractionError('Selected physical/native access is unsupported')
    nx,ny,nl,_,_,_ = snapshot.grid
    if (not isinstance(window,(list,tuple)) or len(window)!=4 or
            any(type(v) is not int for v in window)):
        raise ExtractionError('Require four integer inclusive window bounds')
    x0,y0,x1,y1 = window
    if not (0 <= x0 < x1 < nx and 0 <= y0 < y1 < ny):
        raise ExtractionError('Window outside native grid or degenerate')
    width,height = x1-x0+1,y1-y0+1
    node_count = width*height*nl
    edge_count = nl*((width-1)*height+width*(height-1))+(nl-1)*width*height
    if node_count > solver.MAX_NODES or edge_count > solver.MAX_EDGES:
        raise ExtractionError('Window exceeds declared graph size limits')
    def inside(p):
        return x0<=p[0]<=x1 and y0<=p[1]<=y1
    def name(p):
        return 'p%d_%d_%d'%p
    def layer_name(layer):
        return f'L{layer:02d}'
    selected = set(slots)
    published = _read_segments(segment_text,snapshot,state,selected)
    released, nets, release_manifest = Counter(), [], {}
    for slot in sorted(selected):
        net = snapshot.nets[slot]
        route = published[slot]
        components = _components(route)
        pin_set = set(net['pins'])
        if not any(pin_set <= component for component in components):
            raise ExtractionError('Published route fails native terminal connectivity')
        raw_planar = {_native_link(e) for e in net['planar_step_multiplicity']}
        published_planar = {e for e in route if e[0][2]==e[1][2]}
        if raw_planar != published_planar:
            raise ExtractionError('Published planar union differs from raw STEP support')
        boundary, retained = set(), set()
        for a,b in route:
            if not (inside(a) and inside(b)):
                retained.add((a,b))
                if inside(a)!=inside(b):
                    boundary.add(a if inside(a) else b)
        private = [sorted(name(p) for p in component & boundary)
                   for component in _components(retained) if len(component & boundary)>=2]
        required = {name(p) for p in pin_set if inside(p)} | {name(p) for p in boundary}
        if not required:
            raise ExtractionError('Selected net has no window terminals or crossings')
        weighted_release = step_release = 0
        for edge,multiplicity in net['planar_step_multiplicity'].items():
            a,b = _native_link(edge)
            if inside(a) and inside(b):
                cost = multiplicity*net['demands'][edge[1]]
                released[edge] += cost
                weighted_release += cost
                step_release += multiplicity
        if not step_release:
            raise ExtractionError('Selected net has no released interior planar route')
        release_manifest[str(slot)] = dict(native_name=net['name'],database_id=net['db_id'],
            planar_step_occurrences=step_release,weighted_demand=weighted_release,
            boundary_vertices=len(boundary),private_exterior_components=len(private))
        nets.append(dict(id=str(slot),terminals=sorted(required),boundary_terminals=sorted(name(p) for p in boundary),
            frozen_exterior_components=sorted(private),
            track_demand_by_layer={layer_name(l):net['demands'][l] for l in range(nl)},
            via_track_demand=0,allowed_planar_layers=[layer_name(l) for l in range(net['minimum_layer'],net['maximum_layer']+1)]))
    nodes = [dict(id=name((x,y,l)),x=x,y=y,layer=layer_name(l))
             for l in range(nl) for x in range(x0,x1+1) for y in range(y0,y1+1)]
    edges = []
    for key,(capacity,usage,*_) in snapshot.edges.items():
        a,b = _native_link(key)
        if inside(a) and inside(b):
            fixed = usage-released[key]
            if fixed < 0:
                raise ExtractionError('Selected exact multiset release exceeds raw usage')
            edges.append(dict(id='%s_%d_%d_%d'%key,u=name(a),v=name(b),
                direction='horizontal' if key[0]=='H' else 'vertical',capacity=capacity,fixed_usage=fixed))
    for l in range(nl-1):
        for x in range(x0,x1+1):
            for y in range(y0,y1+1):
                edges.append(dict(id=f'via_{l}_{x}_{y}',u=name((x,y,l)),v=name((x,y,l+1)),
                                  direction='via',capacity=None,fixed_usage=0))
    provenance = dict(raw_sha256=snapshot.sha256,terminal_sha256=state.sha256,
        published_segments_sha256=hashlib.sha256(segment_text.encode()).hexdigest(),
        extractor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        window=list(window),slots=sorted(selected))
    digest = hashlib.sha256(json.dumps(provenance,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    contract = dict(solver.CONTRACT,boundary=solver.EXTERIOR_BOUNDARY,
        exterior_connectivity=solver.EXTERIOR_CONTRACT,vias='unlimited_coarse_edges',nonpreferred='explicit_edges',
        omitted_constraints=sorted(solver.REQUIRED_OMISSIONS | {'physical_via_feasibility','native_search_access_rules'}))
    variables = 2*len(edges)*len(nets)+sum(len(c)-1 for n in nets for c in n['frozen_exterior_components'])
    if variables > solver.MAX_VARIABLES:
        raise ExtractionError('Window/cohort exceeds hard solver variable limit')
    graph = solver.validate_graph(dict(schema_version=2,contract=contract,
        provenance=dict(kind='external_explicit_graph',source_sha256=digest,
            description='Bounded native-derived graph; exact old multiset release, frozen private exterior, optimistic coarse vias; not physical routing'),
        layers=[dict(id=layer_name(l['index']),preferred_direction=l['direction'].lower()) for l in state.layers],
        nodes=nodes,edges=edges,nets=nets))
    return dict(graph=graph,provenance=provenance,selected_admission=admission,release=release_manifest,
        model_variables=variables,
        native_inputs_authenticated=False,physical_acceptance=False,timing_acceptance=False,
        scope='Native-derived restricted coarse graph; fixed exterior, unlimited coarse vias; no native route handoff or physical legality')

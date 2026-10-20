"""Check a partial-route congestion proposal on original whole-grid resources.

No native route is installed. Published frozen exterior links and proposed
interior links must connect every original native pin under coarse via premises.
"""
from collections import defaultdict,deque
from autonomy import corridor_extract,corridor_congestion



def original_zero_permissions(snapshot,extracted):
    result={str(slot):[] for slot in extracted['provenance']['slots']}
    layers={l['id']:i for i,l in enumerate(extracted['graph']['layers'])}
    nodes={n['id']:n for n in extracted['graph']['nodes']}
    for edge in extracted['graph']['edges']:
        if edge['direction']=='via' or edge['capacity']!=0:continue
        a,b=nodes[edge['u']],nodes[edge['v']]
        key=('H' if edge['direction']=='horizontal' else 'V',layers[a['layer']],min(a['x'],b['x']),min(a['y'],b['y']))
        if snapshot.edges[key][0]!=0:raise ValueError('Zero permission capacity differs from native input')
        for slot in extracted['provenance']['slots']:
            if snapshot.nets[slot]['planar_step_multiplicity'].get(key,0)>0:result[str(slot)].append(edge['id'])
    return {name:sorted(ids) for name,ids in result.items()}

def verify(snapshot,state,segment_text,extracted,witness,*,max_window_overflow):
    p=extracted['provenance'];slots=p['slots'];window=p['window']
    rebuilt=corridor_extract.extract(snapshot,state,segment_text,slots=slots,window=window)
    if rebuilt!=extracted:raise ValueError('Proposal model differs from reconstructed native inputs')
    checked=corridor_congestion.check(extracted['graph'],witness,max_overflow=max_window_overflow,zero_capacity_permissions=original_zero_permissions(snapshot,extracted))
    graph=extracted['graph'];nodes={n['id']:n for n in graph['nodes']};layers={l['id']:i for i,l in enumerate(graph['layers'])}
    inside=lambda point:window[0]<=point[0]<=window[2] and window[1]<=point[1]<=window[3]
    original_usage={e:v[1] for e,v in snapshot.edges.items()};proposed=dict(original_usage)
    for edge in graph['edges']:
        if edge['direction']=='via':continue
        a,b=nodes[edge['u']],nodes[edge['v']]
        key=('H' if edge['direction']=='horizontal' else 'V',layers[a['layer']],min(a['x'],b['x']),min(a['y'],b['y']))
        expected=original_usage[key]-sum(snapshot.nets[slot]['planar_step_multiplicity'].get(key,0)*snapshot.nets[slot]['demands'][key[1]] for slot in slots)
        if snapshot.edges[key][0]!=edge['capacity'] or expected!=edge['fixed_usage']:
            raise ValueError('Original capacity or exact old multiset release differs')
        proposed[key]=checked['edge_usage'][edge['id']]
    old_links=corridor_extract._read_segments(segment_text,snapshot,state,set(slots))
    edge_map={e['id']:e for e in graph['edges']};connectivity={}
    for slot in slots:
        links={link for link in old_links[slot] if not all(inside(point) for point in link)}
        for eid in witness[str(slot)]:
            edge=edge_map[eid];a,b=nodes[edge['u']],nodes[edge['v']]
            links.add(tuple(sorted(((a['x'],a['y'],layers[a['layer']]),(b['x'],b['y'],layers[b['layer']])))))
        adjacent=defaultdict(set)
        for a,b in links:adjacent[a].add(b);adjacent[b].add(a)
        pins=set(snapshot.nets[slot]['pins']);reached={min(pins)};queue=deque(reached)
        while queue:
            for other in adjacent[queue.popleft()]-reached:reached.add(other);queue.append(other)
        if not pins<=reached:raise ValueError('Composed route disconnects an original native pin')
        if any(a not in reached or b not in reached for a,b in links):raise ValueError('Composed route has extraneous disconnected links')
        connectivity[str(slot)]=dict(pins=len(pins),coarse_links=len(links),all_pins_connected=True)
    before=sum(max(0,original_usage[e]-v[0]) for e,v in snapshot.edges.items())
    after=sum(max(0,proposed[e]-v[0]) for e,v in snapshot.edges.items())
    if after>=before:raise ValueError('No strict whole-raw-grid overflow improvement')
    changed=[dict(edge=list(e),before=original_usage[e],after=proposed[e],capacity=snapshot.edges[e][0]) for e in sorted(proposed) if proposed[e]!=original_usage[e]]
    return dict(original_full_raw_overflow=before,proposed_full_raw_overflow=after,
        delta=after-before,changed_resources=changed,selected_native_pin_connectivity=connectivity,
        original_capacities_preserved=True,outside_routes_frozen=True,proposal_only=True,
        native_route_installed=False,native_inputs_authenticated=False,physical_acceptance=False,timing_acceptance=False,
        scope='Checked whole-raw-grid arithmetic and coarse pin connectivity of an uninstalled proposal; physical vias/DRC/timing unverified')

"""Exact existence-preserving reduction of finite unit-demand planar graphs.

Prune terminal-free leaves and contract degree-two nonterminal chains.
Default mode keeps physical bends. Topological mode uses synthetic coordinates
and combines parallel chains; original resource paths remain the authority.
Every proposed reduced route expands to original edges and is checked there.
"""
from collections import defaultdict,deque
from copy import deepcopy
from autonomy import corridor_solver as solver


def reduce(graph, *, topological=False):
    if type(topological) is not bool:raise ValueError('topological must be boolean')
    graph=solver.validate_graph(graph)
    if (graph['schema_version']!=1 or len(graph['layers'])!=1 or graph['contract']['vias']!='forbidden' or
            any(e['capacity'] is None or e['fixed_usage']!=0 for e in graph['edges']) or
            any(list(n['track_demand_by_layer'].values())!=[1] for n in graph['nets'])):
        raise ValueError('Reduction requires finite zero-fixed single-layer unit-demand graph')
    nodes={n['id']:n for n in graph['nodes']};edges={e['id']:e for e in graph['edges']}
    adjacent=defaultdict(set)
    for e in edges.values():adjacent[e['u']].add(e['id']);adjacent[e['v']].add(e['id'])
    terminals={t for n in graph['nets'] for t in n['terminals']}
    active=set(edges);queue=deque(n for n in nodes if n not in terminals and len(adjacent[n])<=1)
    while queue:
        node=queue.popleft()
        if node in terminals or len(adjacent[node])>1:continue
        for eid in list(adjacent[node]):
            edge=edges[eid];other=edge['v'] if edge['u']==node else edge['u']
            active.remove(eid);adjacent[node].remove(eid);adjacent[other].remove(eid)
            if other not in terminals and len(adjacent[other])<=1:queue.append(other)
    def other(eid,node):
        edge=edges[eid];return edge['v'] if edge['u']==node else edge['u']
    anchors=set(terminals)
    for name,node in nodes.items():
        if not adjacent[name]:continue
        if len(adjacent[name])!=2:anchors.add(name);continue
        a,b=(nodes[other(eid,name)] for eid in adjacent[name])
        if not topological and not ((a['x']==node['x']==b['x']) or (a['y']==node['y']==b['y'])):
            anchors.add(name)
    # A branch/bend anchors every finite simple grid cycle. Refuse a degenerate
    # parallel-edge cycle instead of silently dropping unsupported geometry.
    visited=set();new_edges=[];paths={};redundant_cycles=[]
    for start in sorted(anchors):
        for first in sorted(adjacent[start]):
            if first in visited:continue
            path=[];current=start;eid=first
            while True:
                if eid in visited:raise ValueError('Unexpected cyclic chain during reduction')
                visited.add(eid);path.append(eid);end=other(eid,current)
                if end in anchors:break
                next_edges=adjacent[end]-{eid}
                if len(next_edges)!=1:raise ValueError('Nonterminal chain lacks unique continuation')
                current=end;eid=next(iter(next_edges))
            if end==start:
                if not topological:raise ValueError('Closed straight chain unsupported')
                redundant_cycles.extend(path);continue
            a,b=nodes[start],nodes[end]
            name='chain_%d'%len(new_edges)
            new_edges.append(dict(id=name,u=start,v=end,direction='horizontal' if topological or a['y']==b['y'] else 'vertical',
                capacity=min(edges[i]['capacity'] for i in path),fixed_usage=0))
            paths[name]=path
    if visited!=active:raise ValueError('Unanchored component unsupported')
    # Parallel disjoint chains are interchangeable unit resources. Aggregate
    # their capacities; expansion allocates each used net to one original path.
    grouped={};combined=[];combined_paths={}
    for edge in new_edges:
        key=tuple(sorted((edge['u'],edge['v'])))
        if key not in grouped:
            name='chain_%d'%len(combined);grouped[key]=name
            combined.append(dict(edge,id=name,capacity=0));combined_paths[name]=[]
        name=grouped[key]
        combined[int(name.split('_')[1])]['capacity']+=edge['capacity']
        combined_paths[name].append(paths[edge['id']])
    new_edges,paths=combined,combined_paths
    original_sha=solver.digest(solver.canonical_bytes(graph))
    reduced=deepcopy(graph);reduced['nodes']=[nodes[n] for n in sorted(anchors)];reduced['edges']=new_edges
    if topological:
        for index,node in enumerate(reduced['nodes']):node.update(x=index,y=0)
        reduced['contract']['omitted_constraints'].append('physical_embedding_replaced_by_topological_indices')
    reduced['provenance']=dict(kind='external_explicit_graph',source_sha256=original_sha,
        description='Exact finite unit-demand chain/dead-end reduction; optional synthetic topology coordinates; expand to original resources required')
    reduced=solver.validate_graph(reduced)
    return dict(schema_version=1,topological=topological,graph=reduced,paths=paths,original_graph_sha256=original_sha,
        removed_redundant_cycle_edges=sorted(redundant_cycles),
        removed_dead_end_edges=sorted(set(edges)-active),
        routing_feasibility_claimed=False,native_inputs_authenticated=False,physical_acceptance=False,timing_acceptance=False,
        scope='Equivalent existence for supplied unit graph only; expand and verify original resources before use')


def expand_and_check(graph,reduction,witness):
    if reduction!=reduce(graph,topological=reduction.get('topological',False)):raise ValueError('Reduction differs from independently reconstructed mapping')
    solver.validate_witness(reduction['graph'],witness)
    original={e['id']:e for e in solver.validate_graph(graph)['edges']}
    remaining={edge:[min(original[i]['capacity'] for i in path) for path in paths]
        for edge,paths in reduction['paths'].items()}
    expanded={}
    for net,selected in sorted(witness.items()):
        route=set()
        for edge in selected:
            index=next((i for i,capacity in enumerate(remaining[edge]) if capacity>0),None)
            if index is None:raise ValueError('No original chain has remaining unit capacity')
            remaining[edge][index]-=1;route.update(reduction['paths'][edge][index])
        expanded[net]=sorted(route)
    checked=solver.validate_witness(graph,expanded)
    return dict(witness=expanded,witness_check=checked,
        routing_feasibility_claimed=False,native_inputs_authenticated=False,physical_acceptance=False,timing_acceptance=False)

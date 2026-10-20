"""Budgeted congestion proposals, not capacity-feasible native routes.

Original capacities stay immutable. Explicit excess variables measure overuse;
independent integer/BFS checks must confirm every returned proposal and budget.
"""
from autonomy import corridor_solver as model,corridor_mip as backend



def _permissions(graph,value):
    nets={n['id'] for n in graph['nets']};edges={e['id']:e for e in graph['edges']}
    if value is None:return {name:set() for name in nets}
    model._keys(value,nets,'zero-capacity permissions')
    result={name:set(model._names(ids,'zero-capacity permissions',set(edges))) for name,ids in value.items()}
    if any(edges[i]['capacity']!=0 or edges[i]['direction']=='via' for ids in result.values() for i in ids):
        raise ValueError('Permissions apply only to explicit zero-capacity planar edges')
    return result

def check(graph,witness,*,max_overflow,zero_capacity_permissions=None):
    graph=model.validate_graph(graph);model._integer(max_overflow,'max_overflow',0)
    permissions=_permissions(graph,zero_capacity_permissions)
    nodes={n['id']:n for n in graph['nodes']};edges={e['id']:e for e in graph['edges']}
    nets={n['id']:n for n in graph['nets']};model._keys(witness,set(nets),'congestion witness')
    usage={i:e['fixed_usage'] for i,e in edges.items()}
    for name,net in nets.items():
        selected=set(model._names(witness[name],name,set(edges)))
        reached=model._connected(edges,selected,net['terminals'][0],net.get('frozen_exterior_components',()))
        if not set(net['terminals'])<=reached:raise ValueError('Required terminal disconnected')
        for i in selected:
            e=edges[i]
            if e['u'] not in reached or e['v'] not in reached:raise ValueError('Disconnected extraneous route')
            if e['direction']!='via':
                if e['capacity']==0 and i not in permissions[name]:raise ValueError('Zero-capacity planar resource lacks per-net permission')
                if nodes[e['u']]['layer'] not in net['allowed_planar_layers']:raise ValueError('Forbidden planar layer')
            usage[i]+=model._edge_demand(net,e,nodes)
    excess={i:max(0,usage[i]-e['capacity']) for i,e in edges.items() if e['capacity'] is not None}
    total=sum(excess.values())
    if total>max_overflow:raise ValueError('Congestion proposal exceeds raw overflow budget')
    return dict(terminal_connectivity_checked=True,original_capacities_preserved=True,
        edge_usage=usage,edge_overflow=excess,total_overflow=total,capacity_feasible=total==0,
        native_inputs_authenticated=False,physical_acceptance=False,timing_acceptance=False)


def solve(graph,*,max_overflow,max_seconds=30,max_memory_mb=1024,max_variables=150000,zero_capacity_permissions=None):
    graph=model.validate_graph(graph);model._integer(max_overflow,'max_overflow',0)
    permissions=_permissions(graph,zero_capacity_permissions)
    max_seconds=model._limit(max_seconds,'max_seconds',300)
    model._integer(max_memory_mb,'max_memory_mb',1,4096);model._integer(max_variables,'max_variables',1,model.MAX_VARIABLES)
    private_count=sum(len(c)-1 for n in graph['nets'] for c in n.get('frozen_exterior_components',()))
    finite=sum(e['capacity'] is not None for e in graph['edges'])
    count=2*len(graph['edges'])*len(graph['nets'])+private_count+finite
    if count>max_variables:raise ValueError('Congestion model exceeds variable bound')
    import ortools
    from ortools.linear_solver import pywraplp
    if ortools.__version__!=backend.SOLVER_VERSION:raise RuntimeError('Require pinned OR-Tools')
    solver=pywraplp.Solver.CreateSolver('SCIP')
    if solver is None or not solver.SolverVersion().startswith(backend.SCIP_VERSION_PREFIX):raise RuntimeError('Require pinned SCIP')
    if not solver.SetNumThreads(1):raise RuntimeError('Rejected worker bound')
    solver.SetTimeLimit(max(1,int(max_seconds*1000)))
    if not solver.SetSolverSpecificParametersAsString(f'limits/memory = {max_memory_mb}\n'):raise RuntimeError('Rejected memory bound')
    nodes={n['id']:n for n in graph['nodes']};edges={e['id']:e for e in graph['edges']}
    incident={i:[] for i in nodes};contributions={i:[] for i in edges};occupancy={}
    for i,e in edges.items():incident[e['u']].append((i,1));incident[e['v']].append((i,-1))
    for ni,net in enumerate(graph['nets']):
        sinks=len(net['terminals'])-1;flow={};private={i:[] for i in nodes}
        for ei,(i,e) in enumerate(edges.items()):
            used=solver.BoolVar(f'x_{ni}_{ei}');f=solver.NumVar(-sinks,sinks,f'f_{ni}_{ei}')
            occupancy[net['id'],i]=used;flow[i]=f
            solver.Add(f<=sinks*used);solver.Add(f>=-sinks*used)
            if e['direction']!='via' and ((e['capacity']==0 and i not in permissions[net['id']]) or nodes[e['u']]['layer'] not in net['allowed_planar_layers']):solver.Add(used==0)
            contributions[i].append(model._edge_demand(net,e,nodes)*used)
        for ci,component in enumerate(net.get('frozen_exterior_components',())):
            for mi,member in enumerate(component[1:]):
                f=solver.NumVar(-sinks,sinks,f'p_{ni}_{ci}_{mi}');private[component[0]].append(f);private[member].append(-f)
        for node in nodes:
            balance=sinks if node==net['terminals'][0] else -1 if node in net['terminals'] else 0
            solver.Add(solver.Sum(sign*flow[i] for i,sign in incident[node])+solver.Sum(private[node])==balance)
    excess=[]
    for ei,(i,e) in enumerate(edges.items()):
        if e['capacity'] is None:continue
        upper=max(0,e['fixed_usage']+sum(model._edge_demand(n,e,nodes) for n in graph['nets'])-e['capacity'])
        over=solver.NumVar(0,upper,f'over_{ei}');solver.Add(over>=e['fixed_usage']+solver.Sum(contributions[i])-e['capacity']);excess.append(over)
    solver.Add(solver.Sum(excess)<=max_overflow)
    weight=len(occupancy)+1;solver.Minimize(weight*solver.Sum(excess)+solver.Sum(occupancy.values()))
    if solver.NumVariables()!=count:raise RuntimeError('Unexpected congestion variable census')
    lp=solver.ExportModelAsLpFormat(False).encode();native=solver.Solve();status=backend._status(native,pywraplp.Solver)
    result=dict(status='PROPOSAL' if status=='FEASIBLE' else status,
        optimal=native==pywraplp.Solver.OPTIMAL,graph_sha256=model.digest(model.canonical_bytes(graph)),
        model_sha256=model.digest(lp),variables=count,constraints=solver.NumConstraints(),solver=solver.SolverVersion(),
        ortools_version=ortools.__version__,max_overflow=max_overflow,zero_capacity_permissions={name:sorted(ids) for name,ids in permissions.items()},
        zero_capacity_planar_policy='only_explicit_per_net_original_permissions',
        limits=dict(wall_seconds=max_seconds,memory_mb=max_memory_mb,variables=max_variables,workers=1,os_memory_limit_enforced=False),
        native_inputs_authenticated=False,physical_acceptance=False,timing_acceptance=False,native_route_installed=False,
        scope='Budgeted overuse proposal in declared graph only; original capacities unchanged, no physical routing claim',
        witness=None,witness_check=None)
    if status=='FEASIBLE':
        witness={}
        for net in graph['nets']:
            selected={i for i in edges if backend._occupancy(occupancy[net['id'],i].solution_value())}
            reached=model._connected(edges,selected,net['terminals'][0],net.get('frozen_exterior_components',()))
            witness[net['id']]=sorted(i for i in selected if edges[i]['u'] in reached)
        result['witness_check']=check(graph,witness,max_overflow=max_overflow,zero_capacity_permissions={name:sorted(ids) for name,ids in permissions.items()});result['witness']=witness
    return result

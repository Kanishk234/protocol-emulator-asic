"""Bounded selection of extra routes satisfying known necessary cut inequalities.

A selected set is a cut-cover proposal, never a feasible routing witness.
The independent checker evaluates original integer capacities directly.
"""
from copy import deepcopy
from autonomy import corridor_solver as contract, corridor_mip as backend


def validate(problem):
    contract._keys(problem,{'schema_version','candidates','cuts','max_additional'},'cut problem')
    if type(problem['schema_version']) is not int or problem['schema_version']!=1:
        raise ValueError('Require cut selection schema1')
    contract._integer(problem['max_additional'],'max_additional',1,128)
    candidates=contract._items(problem['candidates'],'candidates',4096)
    ids=set()
    for candidate in candidates:
        contract._keys(candidate,{'id','old_steps'},'candidate')
        name=contract._name(candidate['id'],'candidate id')
        if name in ids:raise ValueError('Duplicate candidate')
        ids.add(name);contract._integer(candidate['old_steps'],'old_steps',0,10000000)
    cut_ids=set();total_resources=0
    for cut in contract._items(problem['cuts'],'cuts',16,1):
        contract._keys(cut,{'id','required_demand','crossing_demand','resources'},'cut')
        name=contract._name(cut['id'],'cut id')
        if name in cut_ids:raise ValueError('Duplicate cut')
        cut_ids.add(name);contract._integer(cut['required_demand'],'required_demand',0,4096)
        if not isinstance(cut['crossing_demand'],dict) or set(cut['crossing_demand'])!=ids:
            raise ValueError('Cut crossing demands must cover exact candidate inventory')
        for value in cut['crossing_demand'].values():contract._integer(value,'candidate crossing demand',0,1)
        edge_ids=set()
        for resource in contract._items(cut['resources'],'resources',5000):
            total_resources+=1
            contract._keys(resource,{'id','capacity','fixed_usage','releases'},'resource')
            name=contract._name(resource['id'],'resource id')
            if name in edge_ids:raise ValueError('Duplicate cut resource')
            edge_ids.add(name)
            contract._integer(resource['capacity'],'capacity',0,10000000)
            contract._integer(resource['fixed_usage'],'fixed_usage',0,10000000)
            if not isinstance(resource['releases'],dict) or not set(resource['releases'])<=ids:
                raise ValueError('Release inventory differs from candidates')
            for value in resource['releases'].values():contract._integer(value,'release multiplicity',1,10000000)
            if sum(resource['releases'].values())>resource['fixed_usage']:
                raise ValueError('Total candidate release exceeds exact fixed usage')
    if total_resources>10000:raise ValueError('Too many cut resources')
    result=deepcopy(problem)
    result['candidates'].sort(key=lambda c:c['id']);result['cuts'].sort(key=lambda c:c['id'])
    for cut in result['cuts']:cut['resources'].sort(key=lambda r:r['id'])
    return result


def check_selection(problem, selected):
    """Independent arithmetic; no solver, binary activations or floating point."""
    problem=validate(problem);ids={c['id'] for c in problem['candidates']}
    if (not isinstance(selected,list) or any(not isinstance(i,str) for i in selected) or
            len(set(selected))!=len(selected) or not set(selected)<=ids or
            len(selected)>problem['max_additional']):
        raise ValueError('Invalid or oversized selected cohort')
    margins=[]
    for cut in problem['cuts']:
        available=sum(max(0,r['capacity']-r['fixed_usage']+sum(r['releases'].get(i,0) for i in selected))
            for r in cut['resources'])
        required=cut['required_demand']+sum(cut['crossing_demand'][i] for i in selected)
        margins.append(dict(cut=cut['id'],available=available,required=required,margin=available-required))
    if any(row['margin']<0 for row in margins):raise ValueError('Selected cohort violates necessary cut')
    return dict(selected=sorted(selected),cut_margins=margins,
        old_steps=sum(c['old_steps'] for c in problem['candidates'] if c['id'] in selected),
        routing_feasibility_claimed=False,native_inputs_authenticated=False,
        physical_acceptance=False,timing_acceptance=False)


def solve(problem, *, max_seconds=30, max_memory_mb=1024):
    """Minimize extra-net count, then old steps; UNKNOWN remains inconclusive."""
    problem=validate(problem)
    max_seconds=contract._limit(max_seconds,'max_seconds',300)
    contract._integer(max_memory_mb,'max_memory_mb',1,4096)
    import ortools
    from ortools.linear_solver import pywraplp
    if ortools.__version__!=backend.SOLVER_VERSION:raise RuntimeError('Require pinned OR-Tools')
    solver=pywraplp.Solver.CreateSolver('SCIP')
    if solver is None or not solver.SolverVersion().startswith(backend.SCIP_VERSION_PREFIX):
        raise RuntimeError('Require pinned SCIP backend')
    if not solver.SetNumThreads(1):raise RuntimeError('SCIP rejected single worker')
    solver.SetTimeLimit(max(1,int(max_seconds*1000)))
    if not solver.SetSolverSpecificParametersAsString(f'limits/memory = {max_memory_mb}\n'):
        raise RuntimeError('SCIP rejected memory bound')
    # An absent route cannot release any useful resource; selecting it can only
    # increase required demand, cardinality and cost. This pruning is exact.
    useful={i for cut in problem['cuts'] for r in cut['resources'] if r['capacity']>0 for i in r['releases']}
    chosen={c['id']:solver.BoolVar('n_%d'%i) for i,c in enumerate(problem['candidates']) if c['id'] in useful}
    solver.Add(solver.Sum(chosen.values())<=problem['max_additional'])
    nonlinear=0
    for ci,cut in enumerate(problem['cuts']):
        available=[]
        for ri,r in enumerate(cut['resources']):
            cap=r['capacity'];offset=cap-r['fixed_usage']
            terms=[count*chosen[i] for i,count in r['releases'].items() if i in chosen]
            if cap==0:continue  # Releases never exceed fixed usage.
            if not terms:available.append(max(0,offset));continue
            q=offset+solver.Sum(terms)
            if offset>=0:
                available.append(q)  # Nonnegative for every selection; no binary.
                continue
            nonlinear+=1
            active=solver.BoolVar(f'z_{ci}_{ri}');a=solver.NumVar(0,cap,f'a_{ci}_{ri}')
            big=max(cap,-offset)
            solver.Add(a>=q);solver.Add(a<=q+big*(1-active));solver.Add(a<=big*active)
            available.append(a)
        solver.Add(solver.Sum(available)>=cut['required_demand']+
            solver.Sum(cut['crossing_demand'][i]*v for i,v in chosen.items()))
    if solver.NumVariables()>30000:raise ValueError('Cut selection exceeds variable bound')
    weight=1+sum(c['old_steps'] for c in problem['candidates'])
    solver.Minimize(solver.Sum((weight+c['old_steps'])*chosen[c['id']]
        for c in problem['candidates'] if c['id'] in chosen))
    lp=solver.ExportModelAsLpFormat(False).encode();status=solver.Solve()
    result=dict(status=backend._status(status,pywraplp.Solver),
        optimal=status==pywraplp.Solver.OPTIMAL,selected=None,selection_check=None,
        model_sha256=contract.digest(lp),problem_sha256=contract.digest(contract.canonical_bytes(problem)),
        candidates=len(problem['candidates']),retained_candidates=len(chosen),
        nonlinear_resources=nonlinear,variables=solver.NumVariables(),constraints=solver.NumConstraints(),
        solver=solver.SolverVersion(),ortools_version=ortools.__version__,
        limits=dict(wall_seconds=max_seconds,memory_mb=max_memory_mb,workers=1,os_memory_limit_enforced=False),
        routing_feasibility_claimed=False,native_inputs_authenticated=False,
        physical_acceptance=False,timing_acceptance=False,
        scope='Known cut inequalities only; selected routes require fresh admission, cuts and routing solve')
    if result['status']=='FEASIBLE':
        selected=sorted(i for i,v in chosen.items() if backend._occupancy(v.solution_value()))
        result['selection_check']=check_selection(problem,selected);result['selected']=selected
    return result

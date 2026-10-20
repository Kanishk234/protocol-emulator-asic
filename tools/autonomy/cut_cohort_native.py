"""Bind a known-cut selection problem to exact native route multiplicities.

Caller authenticates raw/terminal inputs. Selected additions still require
terminal admission, fresh graph cuts, and an actual routing feasibility solve.
"""
from collections import defaultdict
from autonomy import coarse_global,capacity_cut,cut_cohort,corridor_solver


def build(snapshot,state,*,baseline_slots,records,max_additional=3):
    if not isinstance(records,list) or not 1<=len(records)<=16:
        raise ValueError('Require1..16 authenticated model/cut records')
    _,fixed=coarse_global._state(snapshot,state,baseline_slots)
    nl=snapshot.grid[2]
    candidates={i:n for i,n in snapshot.nets.items() if i not in baseline_slots and
        n['demands']==[1]*nl and n['minimum_layer']==0 and n['maximum_layer']==nl-1}
    releases=defaultdict(dict)
    for slot,net in candidates.items():
        for edge,count in net['planar_step_multiplicity'].items():releases[edge][str(slot)]=count
    cuts=[];hashes=[]
    for index,record in enumerate(records):
        if not isinstance(record,dict) or set(record)!={'model','certificate'}:
            raise ValueError('Require exact model and independently checked certificate')
        model=record['model'];certificate=record['certificate']
        rebuilt=coarse_global.build(snapshot,state,slots=model['provenance']['slots'])
        if model!=rebuilt:raise ValueError('Cut model differs from reconstructed native graph')
        checked=capacity_cut.certify_partition(model['graph'],side_nodes=certificate['side_nodes'])
        if certificate!=checked or not checked['independently_verified_graph_infeasible']:
            raise ValueError('Require genuine independently reproduced cut deficit')
        side_ids=set(checked['side_nodes'])
        side={(n['x'],n['y']) for n in model['graph']['nodes'] if n['id'] in side_ids}
        def crossing(net):return int(len({(x,y) in side for x,y,_ in net['pins']})>1)
        resources=[]
        for edge,data in sorted(snapshot.edges.items()):
            direction,layer,x,y=edge
            if ((x,y) in side)!=((x+(direction=='H'),y+(direction=='V')) in side):
                resources.append(dict(id='%s_%d_%d_%d'%edge,capacity=data[0],fixed_usage=fixed[edge],
                    releases=dict(releases[edge])))
        cuts.append(dict(id='cut_%d'%index,required_demand=sum(crossing(snapshot.nets[i]) for i in baseline_slots),
            crossing_demand={str(i):crossing(n) for i,n in candidates.items()},resources=resources))
        hashes.append(corridor_solver.digest(corridor_solver.canonical_bytes(checked)))
    problem=cut_cohort.validate(dict(schema_version=1,max_additional=max_additional,
        candidates=[dict(id=str(i),old_steps=sum(n['planar_step_multiplicity'].values())) for i,n in candidates.items()],cuts=cuts))
    return dict(problem=problem,baseline_slots=sorted(baseline_slots),
        provenance=dict(raw_sha256=snapshot.sha256,terminal_sha256=state.sha256,cut_sha256=hashes),
        routing_feasibility_claimed=False,native_inputs_authenticated=False,physical_acceptance=False,timing_acceptance=False,
        scope='Exact old-route release and pin-crossing necessary conditions only; proposed additions require fresh admission')

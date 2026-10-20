"""Finite propose/check/refine loop over authenticated native routing diagnostics.

The caller authenticates inputs. Each counterexample is independently checked;
only a proposal with no discovered cut reaches bounded routing feasibility.
"""
from copy import deepcopy
import json
from pathlib import Path
from autonomy import cut_cohort,cut_cohort_native,coarse_global,capacity_cut,corridor_reduce,corridor_mip,corridor_solver


def run(snapshot,state,*,baseline_slots,records,max_additional=4,max_rounds=4,max_variables=100000,output=None):
    corridor_solver._integer(max_rounds,'max_rounds',1,8)
    corridor_solver._integer(max_additional,'max_additional',1,8)
    corridor_solver._integer(max_variables,'max_variables',1,corridor_solver.MAX_VARIABLES)
    if not isinstance(records,list) or not records or len(records)+max_rounds>64:
        raise ValueError('Seed cuts plus bounded rounds must fit64 records')
    records=deepcopy(records)
    directory=Path(output) if output is not None else None
    if directory is not None:directory.mkdir(parents=True,exist_ok=False)
    def save(name,value):
        if directory is not None:
            with (directory/name).open('x') as stream:stream.write(json.dumps(value,indent=2,sort_keys=True)+'\n')
    save('seed-records.json',records)
    result=dict(diagnostic_completed=False,termination='pending',history=[],
        limits=dict(rounds=max_rounds,additional_nets=max_additional,route_variables=max_variables,
            solver_wall_seconds=30,solver_memory_mb=1024,workers=1),
        native_inputs_authenticated=False,physical_acceptance=False,timing_acceptance=False,
        native_route_installed=False,routing_feasibility_claimed=False,
        scope='Finite cut-guided proposals; all native controls authenticated by caller; no installation or promotion')
    try:
        for iteration in range(max_rounds):
            entry=dict(iteration=iteration,known_cuts=len(records));result['history'].append(entry)
            planning=cut_cohort_native.build(snapshot,state,baseline_slots=baseline_slots,records=records,
                max_additional=max_additional)
            entry['planning_model']=planning;save(f'round-{iteration}-planning.json',planning)
            selected=cut_cohort.solve(planning['problem']);entry['selection']=selected;save(f'round-{iteration}-selection.json',selected)
            if selected['status'] not in ('FEASIBLE','INFEASIBLE','UNKNOWN'):
                raise ValueError('Invalid cut selection status')
            if selected['status']!='FEASIBLE':
                result['termination']='selection_'+selected['status'];break
            entry['selection_check']=cut_cohort.check_selection(planning['problem'],selected['selected'])
            slots=list(baseline_slots)+[int(i) for i in selected['selected']]
            model=coarse_global.build(snapshot,state,slots=slots);entry['route_model']=model;save(f'round-{iteration}-route-model.json',model)
            cut=capacity_cut.discover_partition_certificate(model['graph']);entry['new_cut']=cut;save(f'round-{iteration}-cut.json',cut)
            if cut is not None:
                if not cut['independently_verified_graph_infeasible']:
                    raise ValueError('Discovery returned an uncertified cut')
                if any(cut==r['certificate'] for r in records):
                    raise ValueError('Repeated counterexample; refinement made no progress')
                records.append(dict(model=model,certificate=cut));continue
            reduced=corridor_reduce.reduce(model['graph'],topological=True);entry['reduction']=reduced;save(f'round-{iteration}-reduction.json',reduced)
            solved=corridor_mip.solve(reduced['graph'],max_seconds=30,max_memory_mb=1024,max_variables=max_variables)
            entry['routing_solution']=solved;save(f'round-{iteration}-routing-solution.json',solved)
            if solved['status'] not in ('FEASIBLE','INFEASIBLE','UNKNOWN'):
                raise ValueError('Invalid routing result status')
            if solved['graph_sha256']!=corridor_solver.digest(corridor_solver.canonical_bytes(reduced['graph'])):
                raise ValueError('Routing result graph identity differs')
            if any(solved.get(k) is not False for k in ('native_inputs_authenticated','physical_acceptance','timing_acceptance')):
                raise ValueError('Routing result exceeds diagnostic authority')
            if solved['status']=='FEASIBLE':
                expanded=corridor_reduce.expand_and_check(model['graph'],reduced,solved['witness'])
                entry['expanded_witness']=expanded;save(f'round-{iteration}-expanded-witness.json',expanded)
                entry['original_layer_check']=coarse_global.allocate_and_check(snapshot,state,model,expanded['witness']);save(f'round-{iteration}-original-layer-check.json',entry['original_layer_check'])
            result['termination']='routing_'+solved['status'];break
        else:result['termination']='round_limit'
        result['diagnostic_completed']=True
    except Exception as exc:
        result['termination']='error';result['error']=type(exc).__name__+': '+str(exc)
    save('summary.json',result)
    return result

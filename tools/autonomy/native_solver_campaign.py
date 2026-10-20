"""Finite, read-only native-derived solver campaign; never dispatch EDA or promote.

Caller fetches API identity/artifacts. Audit explicit run/source/attempt and all
native controls before constructing either model. UNKNOWN is an honest result.
"""
import argparse
import hashlib
import json
from pathlib import Path

from autonomy import repair_evidence,native_corridor,native_terminals
from autonomy import corridor_extract,coarse_global,corridor_solver,capacity_cut

RAW_SHA='1859f6fdaffad9977ab4025867332a5835e68f50b86405719447b1b3c1aa07e6'
TERMINAL_SHA='90be2ecef64627ed67b1c4df920f86f673cac1bcdae4fef4db9587a3e79a18d3'
COHORT=[32,120,123,124,387]
WINDOW=[8,0,17,9]


def _write(directory,name,value):
    with (directory/name).open('x') as stream:
        stream.write(json.dumps(value,indent=2,sort_keys=True)+'\n')


def run(bundle,identity,*,revision,run_id,attempt,output,backend='cp_sat'):
    if backend not in ('cp_sat','scip'):raise ValueError('Unsupported bounded solver backend')
    # This parses every actual control/export; never trust stored collector booleans.
    audited=repair_evidence.audit(bundle,identity,revision=revision,run_id=run_id,attempt=attempt,
        candidate=True,native_corridor=True,native_terminals=True)
    stage,= (Path(bundle)/'default_identity/replay').glob('*-openroad-globalrouting')
    rp=stage/'corridor-initial/native-corridor.tsv';tp=stage/'terminal-initial/native-terminals.tsv'
    sp=stage/'initial-segments.txt'
    raw_bytes,terminal_bytes,segment_bytes=rp.read_bytes(),tp.read_bytes(),sp.read_bytes()
    if hashlib.sha256(raw_bytes).hexdigest()!=RAW_SHA or hashlib.sha256(terminal_bytes).hexdigest()!=TERMINAL_SHA:
        raise ValueError('Campaign requires exact authenticated initial native/terminal checkpoint')
    if hashlib.sha256(segment_bytes).hexdigest()!=repair_evidence.hosted.EXPECTED_SEGMENTS:
        raise ValueError('Campaign initial published segments differ')
    snapshot=native_corridor.parse_bytes(raw_bytes);terminals=native_terminals.parse_bytes(terminal_bytes)
    local=corridor_extract.extract(snapshot,terminals,segment_bytes.decode('utf-8'),slots=COHORT,window=WINDOW)
    global_model=coarse_global.build(snapshot,terminals,slots=COHORT)
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    _write(output,'input-audit.json',audited)
    _write(output,'local-model.json',local);_write(output,'global-model.json',global_model)
    if backend=='cp_sat':solve=corridor_solver.solve
    else:
        from autonomy import corridor_mip
        solve=corridor_mip.solve
    summary=dict(schema_version=1,diagnostic_completed=False,backend=backend,
        native_run=str(run_id),native_revision=revision,native_attempt=attempt,
        native_result_sha256=audited['result_sha256'],cohort=list(COHORT),window=list(WINDOW),
        campaign_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        native_inputs_authenticated=False,physical_acceptance=False,timing_acceptance=False,
        scope='Two bounded declared-graph experiments; no native guide installation, physical signoff or automatic promotion')
    try:
        for name,model in [('local',local),('global',global_model)]:
            result=solve(model['graph'],max_seconds=30,max_memory_mb=1024,max_variables=100000)
            if result['status'] not in ('FEASIBLE','INFEASIBLE','UNKNOWN'):
                raise ValueError('Unsupported solver status; no classification')
            if (result['graph_sha256']!=corridor_solver.digest(corridor_solver.canonical_bytes(model['graph'])) or
                    any(result.get(k) is not False for k in ('native_inputs_authenticated','physical_acceptance','timing_acceptance'))):
                raise ValueError('Solver result graph identity or scope contradicts experiment')
            _write(output,name+'-solution.json',result)
            summary[name]=dict(status=result['status'],graph_sha256=result['graph_sha256'],model_size=result['model_size'])
            if name=='local':
                cut=capacity_cut.certify(model['graph'],axis='x',coordinate=16)
                if cut['independently_verified_graph_infeasible'] and result['status']=='FEASIBLE':
                    raise ValueError('Solver witness contradicts independently checked capacity cut')
                _write(output,'local-cut.json',cut)
                summary[name]['independent_cut_infeasible']=cut['independently_verified_graph_infeasible']
            else:
                cut=capacity_cut.discover_partition_certificate(model['graph'])
                _write(output,'global-cut.json',cut)
                summary[name]['independent_cut_infeasible']=cut is not None
                if cut is not None and result['status']=='FEASIBLE':
                    raise ValueError('Solver witness contradicts independent global capacity cut')
                if result['status']=='FEASIBLE':
                    checked=coarse_global.allocate_and_check(snapshot,terminals,model,result['witness'])
                    _write(output,'global-checked-layers.json',checked)
                    summary[name]['proposed_raw_overflow']=checked['proposed_raw_overflow']
                    summary[name]['native_route_installed']=False
        summary['diagnostic_completed']=True
    except Exception as exc:
        summary['error']=str(exc)
        raise
    finally:
        _write(output,'summary.json',summary)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('bundle',type=Path);p.add_argument('--identity',type=Path,required=True)
    p.add_argument('--revision',required=True);p.add_argument('--run-id',required=True)
    p.add_argument('--attempt',type=int,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--backend',choices=['cp_sat','scip'],default='cp_sat')
    a=p.parse_args()
    print(json.dumps(run(a.bundle,json.loads(a.identity.read_text()),revision=a.revision,
        run_id=a.run_id,attempt=a.attempt,output=a.output,backend=a.backend),indent=2,sort_keys=True))


if __name__=='__main__':main()

"""Authenticate native controls, then run a finite cut-guided joint-cohort trial.

No EDA, guide installation or promotion. Four rounds, up to five extra nets,
30s/1024MB per solve; explicit150k route-variable cap inside500k hard bound.
"""
import argparse
import base64
import zlib
import hashlib
import json
from pathlib import Path
from autonomy import native_solver_campaign as fixed,coarse_global,capacity_cut,cut_refinement


MAX_SEED_BYTES=2000000
MAX_ENCODED_BYTES=50000


def encode_seeds(snapshot,state,records):
    """Portable bounded constraints only; no raw native data or stored booleans."""
    if not isinstance(records,list) or not 1<=len(records)<=32:
        raise ValueError('Require1..32 seed constraints')
    payload=dict(schema_version=1,raw_sha256=snapshot.sha256,terminal_sha256=state.sha256,
        cuts=[dict(slots=r['model']['provenance']['slots'],side_nodes=r['certificate']['side_nodes']) for r in records])
    raw=json.dumps(payload,sort_keys=True,separators=(',',':')).encode()
    if len(raw)>MAX_SEED_BYTES:raise ValueError('Seed payload exceeds decoded byte bound')
    encoded=base64.b64encode(zlib.compress(raw)).decode('ascii')
    if len(encoded)>MAX_ENCODED_BYTES:raise ValueError('Seed payload exceeds workflow input bound')
    return encoded


def decode_seeds(snapshot,state,encoded):
    """Rebuild every model and recertify its deficit; never trust prior statuses."""
    if not isinstance(encoded,str) or not 1<=len(encoded)<=MAX_ENCODED_BYTES:
        raise ValueError('Invalid seed input length')
    compressed=base64.b64decode(encoded,validate=True)
    decoder=zlib.decompressobj();raw=decoder.decompress(compressed,MAX_SEED_BYTES+1)
    if len(raw)>MAX_SEED_BYTES or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ValueError('Invalid, trailing, or oversized seed archive')
    payload=json.loads(raw)
    if not isinstance(payload,dict) or set(payload)!={'schema_version','raw_sha256','terminal_sha256','cuts'}:
        raise ValueError('Invalid seed schema fields')
    if type(payload['schema_version']) is not int or payload['schema_version']!=1:
        raise ValueError('Invalid seed version')
    if payload['raw_sha256']!=snapshot.sha256 or payload['terminal_sha256']!=state.sha256:
        raise ValueError('Seed checkpoint identity differs')
    if not isinstance(payload['cuts'],list) or not 1<=len(payload['cuts'])<=32:
        raise ValueError('Require1..32 seed constraints')
    records=[]
    for cut in payload['cuts']:
        if not isinstance(cut,dict) or set(cut)!={'slots','side_nodes'}:
            raise ValueError('Invalid seed cut fields')
        model=coarse_global.build(snapshot,state,slots=cut['slots'])
        certificate=capacity_cut.certify_partition(model['graph'],side_nodes=cut['side_nodes'])
        if not certificate['independently_verified_graph_infeasible']:
            raise ValueError('Imported seed is not a certified capacity deficit')
        records.append(dict(model=model,certificate=certificate))
    return records


def run(bundle,identity,*,revision,run_id,attempt,output,seed_manifest=''):
    audited,snapshot,terminals,_=fixed.load_inputs(bundle,identity,revision=revision,run_id=run_id,attempt=attempt)
    seed=coarse_global.build(snapshot,terminals,slots=fixed.COHORT)
    cut=capacity_cut.discover_partition_certificate(seed['graph'])
    if cut is None:raise ValueError('Expected authenticated baseline capacity deficit not reproduced')
    records=decode_seeds(snapshot,terminals,seed_manifest) if seed_manifest else [dict(model=seed,certificate=cut)]
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    fixed._write(output,'input-audit.json',audited)
    summary=dict(diagnostic_completed=False,native_run=str(run_id),native_revision=revision,native_attempt=attempt,
        native_result_sha256=audited['result_sha256'],baseline_slots=list(fixed.COHORT),seed_count=len(records),
        source_sha256={name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest()
            for name in ('native_joint_campaign.py','native_solver_campaign.py','cut_refinement.py','cut_cohort.py','cut_cohort_native.py','corridor_reduce.py')},
        native_inputs_authenticated=False,physical_acceptance=False,timing_acceptance=False,native_route_installed=False,
        scope='Four-round authenticated cut-guided diagnostic; no physical signoff or automatic promotion')
    try:
        result=cut_refinement.run(snapshot,terminals,baseline_slots=fixed.COHORT,
            records=records,max_additional=5,max_rounds=4,max_variables=150000,
            output=output/'refinement')
        summary.update(diagnostic_completed=result['diagnostic_completed'],termination=result['termination'],
            rounds=len(result['history']))
        if not result['diagnostic_completed']:raise RuntimeError(result.get('error','Joint refinement failed'))
    except Exception as exc:
        summary['error']=type(exc).__name__+': '+str(exc)
        raise
    finally:fixed._write(output,'summary.json',summary)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('bundle',type=Path);p.add_argument('--identity',type=Path,required=True)
    p.add_argument('--revision',required=True);p.add_argument('--run-id',required=True)
    p.add_argument('--attempt',type=int,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--seed-manifest',default='')
    a=p.parse_args();print(json.dumps(run(a.bundle,json.loads(a.identity.read_text()),revision=a.revision,
        run_id=a.run_id,attempt=a.attempt,output=a.output,seed_manifest=a.seed_manifest),indent=2,sort_keys=True))


if __name__=='__main__':main()

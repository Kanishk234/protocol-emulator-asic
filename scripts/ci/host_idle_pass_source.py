"""Restore the exact green local-route checkpoint; never repeat physical edits."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
from c_select_pass_source import CORNERS, require_gates
from route_segment_audit import parse
from route_attachment_audit import atomic_routes
from local_route_patch import audit


def route_scope(before_text, after_text, ledger, reference, policy):
    before=atomic_routes(parse(before_text));after=atomic_routes(parse(after_text))
    assert len(before)==len(after)==reference['routed_nets']
    assert hashlib.sha256(json.dumps(before,sort_keys=True,separators=(',',':')).encode()).hexdigest()==reference['original_atomic_sha256']
    assert hashlib.sha256(json.dumps(ledger,sort_keys=True,separators=(',',':')).encode()).hexdigest()==policy['ledger_sha256']
    def numeric(routes):
        return {n:[((a[0],a[1],int(a[2][5:])),(b[0],b[1],int(b[2][5:]))) for a,b in rows] for n,rows in routes.items()}
    audit(numeric(before),numeric(after),ledger)
    return dict(route_scope_revalidated=True,routed_nets=len(after),
                changed_nets=sorted(n for n in before if before[n]!=after[n]))


def restore(root, manifest, run, artifact, reference, policy):
    root=Path(root).resolve()
    for name,actual in (('run',run),('artifact',artifact)):
        assert all(actual.get(k)==v for k,v in manifest[name].items()), 'Wrong green source provenance'
    for name,digest in manifest['files'].items():
        p=PurePosixPath(name)
        assert not p.is_absolute() and '..' not in p.parts
        path=root/name
        assert path.resolve().is_relative_to(root)
        assert hashlib.sha256(path.read_bytes()).hexdigest()==digest, 'Green source file hash mismatch: '+name
    read=lambda name:json.loads((root/name).read_text())
    base=root/'runs/route-reopen-calibration'
    gates=read('runs/route-reopen-calibration/final_gates.json');require_gates(gates)
    coverage=read('runs/route-reopen-calibration/native_coverage.json')
    assert coverage['all_routed_nets_connected_and_pins_covered'] is True
    assert coverage['independent_process'] is True and coverage['exact_route_roundtrip'] is True
    assert coverage['routed_nets']==45192
    signoff=read('runs/host-idle-signoff-audit/qualification.json')
    assert signoff['qualified'] is True and signoff['edited'] is True and signoff['failures']==[]
    intervention=read('runs/route-reopen-calibration/intervention.json')
    assert intervention['added_diodes']==6 and intervention['clock_net_changed'] is False
    for name in ('placement_checked','post_router_placement_checked',
                 'post_router_placement_and_connections_verified',
                 'exact_original_edges_preserved_except_two_detours'):
        assert intervention[name] is True
    assert set(intervention['selected_actual_crossing_nets'])=={d['net'] for d in policy['detours']}
    ledger=intervention['local_patch_ledger']
    assert ledger==read('runs/route-reopen-calibration/local_patch_plan.json')['ledger']
    scope=route_scope((base/'before.segments').read_text(),(base/'after.segments').read_text(),ledger,reference,policy)
    assert scope['routed_nets']==45192
    # Historical geometry_result used compare() without an allowlist; its
    # "unexpected" labels are not a scope proof. Recompute against the complete
    # frozen source and reviewed ledger rather than altering historical evidence.
    geometry=read('runs/route-reopen-calibration/geometry_result.json')
    assert sorted(geometry['changed_nets'])==scope['changed_nets']
    state=read('runs/route-reopen-calibration/state_out.json')
    for key,suffix in (('odb','odb'),('def','def'),('nl','nl.v'),('pnl','pnl.v')):
        assert Path(state[key])==Path.cwd()/'runs/route-reopen-calibration'/('calibrated.'+suffix)
    for path,digest in ((Path(state['sdc']),manifest['sdc_sha256']),
                        (Path('src/signoff.sdc'),manifest['signoff_sdc_sha256'])):
        assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==digest
    evidence=read('runs/stock-corner-audit/read_only_audit.json')
    assert evidence['source_run']==manifest['base_source_run']==reference['source_run']==policy['source_run']
    assert evidence['fresh_corner_metrics']==gates['corners']
    assert evidence['fresh_antenna_metrics']==gates['antenna']
    for name,digest in evidence['unchanged_physical_view_hashes'].items():
        rel=str(Path(name).relative_to(Path.cwd())) if Path(name).is_absolute() else name
        if rel=='runs/stock-official-baseline/44-openroad-resizertimingpostgrt/tt_um_tripwire.sdc':
            assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest
        else:assert manifest['files'][rel]==digest
    log=(root/'runs/route-reopen.log').read_text()
    assert not re.search(r'(?m)^\[ERROR\b',log)
    totals=re.findall(r'(?m)^Total\s+\d+\s+(\d+)\s+[0-9.]+%\s+\d+\s*/\s*\d+\s*/\s*(\d+)\s*$',log)
    assert totals and int(totals[-1][0])>0 and int(totals[-1][1])==0
    target=Path('runs/route-reopen-calibration');assert not target.exists()
    shutil.copytree(base,target)
    shutil.copy2(root/'runs/route-reopen.log','runs/route-reopen.log')
    (target/'native_coverage.json').unlink()
    (target/'coverage-readback.segments').unlink(missing_ok=True)
    Path('runs/host-idle-pass-restoration.json').write_text(json.dumps(dict(
        source_run=run['id'],source_sha=run['head_sha'],artifact_id=artifact['id'],
        physical_repairs_repeated=False,checkpoint_state=str(target/'state_out.json'),
        historical_compare_without_allowlist=True,**scope,official_flow_qualified=False),indent=2)+'\n')
    return target/'state_out.json'

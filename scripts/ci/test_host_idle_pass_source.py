import hashlib
import json
from pathlib import Path
import pytest
import host_idle_pass_source as module
from test_c_select_pass_source import fixture as gates_fixture
from route_attachment_audit import atomic_routes
from route_segment_audit import parse


def test_actual_route_scope_is_verified_without_trusting_compare_flags():
    before='n\n(\n3600 3600 Metal2 3600 10800 Metal2\n)\n'
    after=before.replace(')\n','3600 10800 Metal1 3600 10800 Metal2\n)\n')
    ledger=[dict(net='n',removed=[],added=[((3600,10800,1),(3600,10800,2))])]
    sha=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    ref=dict(routed_nets=1,original_atomic_sha256=sha(atomic_routes(parse(before))))
    policy=dict(ledger_sha256=sha(ledger))
    assert module.route_scope(before,after,ledger,ref,policy)['changed_nets']==['n']
    with pytest.raises(ValueError):
        module.route_scope(before,after.replace(')\n','3600 3600 Metal2 3600 3600 Metal3\n)\n'),ledger,ref,policy)


@pytest.mark.parametrize('fault',[None,'run','hash','coverage','clock','placement','state','sdc','signoff','metrics','control'])
def test_exact_green_restore_and_refusal_before_copy(tmp_path,monkeypatch,fault):
    monkeypatch.chdir(tmp_path)
    root=Path('passing');base=root/'runs/route-reopen-calibration';base.mkdir(parents=True)
    sdc=Path('runs/stock-official-baseline/44-openroad-resizertimingpostgrt/tt_um_tripwire.sdc')
    sdc.parent.mkdir(parents=True);sdc.write_text('clock20')
    Path('src').mkdir();Path('src/signoff.sdc').write_text('signoff20')
    state={'sdc':str(sdc.resolve())}
    for key,suffix in [('odb','odb'),('def','def'),('nl','nl.v'),('pnl','pnl.v')]:
        state[key]=str(Path('runs/route-reopen-calibration', 'calibrated.'+suffix).resolve())
        (base/('calibrated.'+suffix)).write_text(key)
    if fault=='state':state['odb']='/wrong.odb'
    def write(name,data):
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data))
    write('runs/route-reopen-calibration/state_out.json',state)
    gates=gates_fixture()
    if fault=='control':gates['edited']=False
    write('runs/route-reopen-calibration/final_gates.json',gates)
    write('runs/route-reopen-calibration/native_coverage.json',dict(
        all_routed_nets_connected_and_pins_covered=True,independent_process=True,exact_route_roundtrip=True,
        routed_nets=1 if fault=='coverage' else 45192))
    write('runs/host-idle-signoff-audit/qualification.json',dict(qualified=fault!='signoff',edited=True,failures=[]))
    write('runs/route-reopen-calibration/intervention.json',dict(added_diodes=6,
        clock_net_changed=fault=='clock',placement_checked=fault!='placement',post_router_placement_checked=True,
        post_router_placement_and_connections_verified=True,exact_original_edges_preserved_except_two_detours=True,
        selected_actual_crossing_nets=['data'],local_patch_ledger=[]))
    write('runs/route-reopen-calibration/local_patch_plan.json',{'ledger':[]})
    write('runs/route-reopen-calibration/geometry_result.json',{'changed_nets':[],'unchanged_routes_preserved':False})
    for n in ('before.segments','after.segments'):(base/n).write_text('fixture')
    hashes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in base.iterdir() if p.name.startswith('calibrated.') or p.name=='state_out.json'}
    hashes[str(sdc.resolve())]=hashlib.sha256(sdc.read_bytes()).hexdigest()
    metrics=json.loads(json.dumps(gates['corners']))
    if fault=='metrics':metrics[next(iter(metrics))][next(iter(metrics[next(iter(metrics))]))]=.2
    write('runs/stock-corner-audit/read_only_audit.json',dict(source_run=42305323874,fresh_corner_metrics=metrics,
        fresh_antenna_metrics=gates['antenna'],unchanged_physical_view_hashes=hashes))
    (root/'runs/route-reopen.log').write_text('Total 100 10 10.0% 0 / 0 / 0\n')
    manifest=dict(run={'id':1},artifact={'id':2},base_source_run=42305323874,files={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob('*') if p.is_file()},sdc_sha256=hashlib.sha256(sdc.read_bytes()).hexdigest(),
        signoff_sdc_sha256=hashlib.sha256(Path('src/signoff.sdc').read_bytes()).hexdigest())
    if fault=='sdc':sdc.write_text('relaxed')
    if fault=='hash':(base/'calibrated.odb').write_text('corrupt')
    monkeypatch.setattr(module,'route_scope',lambda *a:dict(route_scope_revalidated=True,routed_nets=45192,changed_nets=[]))
    args=(root,manifest,{'id':0 if fault=='run' else 1,'head_sha':'tested'},{'id':2},
          {'routed_nets':45192,'source_run':42305323874},{'detours':[{'net':'data'}],'source_run':42305323874})
    if fault:
        with pytest.raises(AssertionError):module.restore(*args)
        assert not Path('runs/route-reopen-calibration').exists()
    else:
        assert module.restore(*args).is_file()
        assert not Path('runs/route-reopen-calibration/native_coverage.json').exists()
        assert Path('runs/host-idle-pass-restoration.json').is_file()

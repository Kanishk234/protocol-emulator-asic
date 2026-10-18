import hashlib
import json
from pathlib import Path
import pytest
import native_post_antenna_gl as target
from native_stock_screen import configure
from native_post_antenna_screen import configure as final_configure


def fixture(tmp_path):
    route=tmp_path/'runs/native-post-timing-antenna-route/qualified-route'
    step=route/'drt/1-openroad-detailedrouting';step.mkdir(parents=True)
    (route/'gates.json').write_text(json.dumps(dict(source_run=39141162581,qualified=True,
        minimum_fast_hold_ns=.05,repair_repeated=False,official_signoff=False)))
    (route/'extracted_gates.json').write_text(json.dumps(dict(source_run=39141162581,
        qualified=True,minimum_fast_hold_ns=.05,official_signoff=False)))
    nl=step/'tt_um_tripwire.nl.v'
    nl.write_text('module tt_um_tripwire; RM_IHPSG13_1P_512x16_c2_bm_bist ram (); endmodule\n')
    (step/'state_out.json').write_text(json.dumps(dict(metrics={'route__drc_errors':0},
        nl='/runner/runs/native-post-timing-antenna-route/qualified-route/drt/1-openroad-detailedrouting/tt_um_tripwire.nl.v')))
    cfg=final_configure(configure(dict(CLOCK_PERIOD=20,PL_TARGET_DENSITY_PCT=56),
        'AREA 1',Path('/runner/src/signoff.sdc'),hold_target=.10,clock_cluster=8))
    src=tmp_path/'src';src.mkdir()
    (src/'config_native_stock.json').write_text(json.dumps(cfg))
    (src/'config_electrical_incremental_route.json').write_text(json.dumps(cfg))
    # The real single-step DRT config omits synthesis-only variables.
    (step/'config.json').write_text(json.dumps({k:cfg[k] for k in
        ('CLOCK_PERIOD','GRT_ADJUSTMENT','GRT_ALLOW_CONGESTION','PNR_SDC_FILE')}))
    extracted=tmp_path/'runs/extracted-timing';sta=extracted/'11-openroad-stapostpnr';sta.mkdir(parents=True)
    summary={f'timing__{kind}__ws__corner:{c}':(.08 if kind=='hold' else 0)
             for c in target.CORNERS for kind in ('setup','hold')}
    (extracted/'corner_summary.json').write_text(json.dumps(summary))
    ant=extracted/'2-openroad-checkantennas';ant.mkdir()
    (ant/'or_metrics_out.json').write_text(json.dumps({'antenna__violating__nets':0,'antenna__violating__pins':0}))
    for c in target.CORNERS:
        d=sta/c;d.mkdir()
        (d/'checks.rpt').write_text(c+'\nmax slew violation count 0\nmax fanout violation count 0\nmax cap violation count 0\n')
    run=dict(id=target.ROUTE_RUN,head_sha=target.ROUTE_SHA,head_branch='main',conclusion='success',
             path='.github/workflows/gds-native-post-timing-antenna-route.yaml')
    hashes=[hashlib.sha256(p.read_bytes()).hexdigest() for p in
            (nl,src/'config_electrical_incremental_route.json',step/'config.json')]
    return run,route,step,hashes


@pytest.mark.parametrize('fault',[None,'running','run','head','path','hash','no_recipe_review',
    'no_step_review','changed_netlist','changed_config','source','drc','extracted_gate',
    'hold','setup','electrical','antenna','missing_corner','full_recipe'])
def test_exact_completed_route_and_measured_evidence_required(tmp_path,fault):
    run,route,step,hashes=fixture(tmp_path)
    extracted=tmp_path/'runs/extracted-timing'
    if fault=='running':run['conclusion']=''
    if fault=='run':run['id']=1
    if fault=='head':run['head_sha']='other'
    if fault=='path':run['path']='wrong'
    if fault=='hash':hashes[0]='0'*64
    if fault=='no_recipe_review':hashes[1]=''
    if fault=='no_step_review':hashes[2]=''
    if fault=='changed_netlist':(step/'tt_um_tripwire.nl.v').write_text('changed')
    if fault=='changed_config':(step/'config.json').write_text('{}')
    if fault in ('source','extracted_gate','drc'):
        path=route/('gates.json' if fault=='source' else 'extracted_gates.json')
        if fault=='drc':path=step/'state_out.json'
        data=json.loads(path.read_text())
        if fault=='drc':data['metrics']['route__drc_errors']=1
        elif fault=='source':data['source_run']=1
        else:data['qualified']=False
        path.write_text(json.dumps(data))
    if fault in ('hold','setup'):
        path=extracted/'corner_summary.json';data=json.loads(path.read_text())
        data[f'timing__{fault}__ws__corner:{target.CORNERS[0]}']=.049 if fault=='hold' else -.001
        path.write_text(json.dumps(data))
    if fault=='antenna':
        (extracted/'2-openroad-checkantennas/or_metrics_out.json').write_text(json.dumps({'antenna__violating__nets':1,'antenna__violating__pins':1}))
    if fault in ('missing_corner','electrical'):
        path=extracted/'11-openroad-stapostpnr'/target.CORNERS[1]/'checks.rpt'
        if fault=='missing_corner':path.unlink()
        else:path.write_text(target.CORNERS[1]+'\nmax fanout\ndriver/X 8 9 (VIOLATED)\nmax slew violation count 0\nmax fanout violation count 1\nmax cap violation count 0\n')
    if fault=='full_recipe':(tmp_path/'src/config_native_stock.json').write_text('{}')
    if fault:
        with pytest.raises((ValueError,FileNotFoundError)):target.validate(tmp_path,run,*hashes)
    else:
        result=target.validate(tmp_path,run,*hashes)
        assert result['route_run']==target.ROUTE_RUN
        assert result['functional_simulation_only'] is True and result['official_signoff'] is False


def test_workflow_is_manual_and_preserves_expanded_suite():
    import yaml
    root=Path(__file__).resolve().parents[2]
    w=yaml.safe_load((root/'.github/workflows/l3-native-post-timing-antenna-routed-gl.yaml').read_text())
    trigger=w.get('on',w.get(True))
    assert set(trigger)=={'workflow_dispatch'}
    assert set(trigger['workflow_dispatch']['inputs'])=={'reviewed_netlist_sha','reviewed_recipe_sha','reviewed_step_config_sha'}
    steps=w['jobs']['l3']['steps']
    d=next(s['with'] for s in steps if 'download-artifact@' in s.get('uses',''))
    assert d['run-id']==target.ROUTE_RUN
    assert d['name']==f'gds-native-post-timing-antenna-route-{target.ROUTE_RUN}'
    commands='\n'.join(s.get('run','') for s in steps)
    assert 'from native_post_antenna_gl import validate' in commands
    assert 'iverilog_13.0-1_amd64.deb' in commands
    assert 'COCOTB_TEST_MODULES=test_l3' in commands

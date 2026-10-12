import hashlib
import json
from pathlib import Path
import pytest
from native_route_gl import validate_electrical


def fixture(root):
    route=root/'runs/electrical-incremental-route';step=route/'drt/1-openroad-detailedrouting';step.mkdir(parents=True)
    run=dict(id=38305592967,head_sha='2d73b6fe4b3ee22337fe7db2240cda7761dcda5e',head_branch='main',conclusion='success',path='.github/workflows/gds-electrical-incremental-route.yaml')
    gate=dict(source_run=38304235648,qualified=True,minimum_fast_hold_ns=.05,official_signoff=False)
    (route/'gates.json').write_text(json.dumps(dict(gate,repair_repeated=False)));(route/'extracted_gates.json').write_text(json.dumps(gate))
    (step/'state_out.json').write_text(json.dumps(dict(metrics={'route__drc_errors':0},nl='/runner/runs/electrical-incremental-route/drt/1-openroad-detailedrouting/tt_um_tripwire.nl.v')))
    recipe=dict(CLOCK_PERIOD=20,GRT_ADJUSTMENT=.16,GRT_ALLOW_CONGESTION=False,SYNTH_STRATEGY='AREA 1',GRT_RESIZER_HOLD_SLACK_MARGIN=.125,PNR_SDC_FILE='/runner/src/signoff.sdc')
    (root/'src').mkdir();(root/'src/config_electrical_incremental_route.json').write_text(json.dumps(recipe));(step/'config.json').write_text(json.dumps(recipe))
    nl=step/'tt_um_tripwire.nl.v';nl.write_text('module tt_um_tripwire; RM_IHPSG13_1P_512x16_c2_bm_bist s(); endmodule')
    return run,hashlib.sha256(nl.read_bytes()).hexdigest(),route,step


@pytest.mark.parametrize('fault',[None,'run','head','failed','hash','missing_hash','extracted','drc','path','recipe','netlist'])
def test_only_reviewed_complete_qualified_route_accepted(tmp_path,fault):
    run,digest,route,step=fixture(tmp_path)
    if fault=='run':run['id']=1
    if fault=='head':run['head_sha']='wrong'
    if fault=='failed':run['conclusion']='failure'
    if fault=='hash':digest='0'*64
    if fault=='missing_hash':digest=None
    if fault=='extracted':
        p=route/'extracted_gates.json';data=json.loads(p.read_text());data['qualified']=False;p.write_text(json.dumps(data))
    if fault in ('drc','path'):
        p=step/'state_out.json';data=json.loads(p.read_text())
        if fault=='drc':data['metrics']['route__drc_errors']=1
        else:data['nl']='/old/netlist.v'
        p.write_text(json.dumps(data))
    if fault=='recipe':
        p=step/'config.json';data=json.loads(p.read_text());data['CLOCK_PERIOD']=25;p.write_text(json.dumps(data))
    if fault=='netlist':(step/'tt_um_tripwire.nl.v').write_text('changed')
    if fault:
        with pytest.raises(ValueError):validate_electrical(tmp_path,run,digest)
    else:
        result=validate_electrical(tmp_path,run,digest)
        assert result['sha256']==digest and result['official_signoff'] is False


def test_manual_workflow_requires_reviewed_hash_and_fixed_source():
    import yaml
    p=Path(__file__).resolve().parents[2]/'.github/workflows/l3-electrical-routed-gl.yaml'
    w=yaml.safe_load(p.read_text());trigger=w.get('on',w.get(True))
    assert set(trigger)=={'workflow_dispatch'}
    assert trigger['workflow_dispatch']['inputs']['reviewed_netlist_sha']['required']
    steps=w['jobs']['l3']['steps'];d=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert d['with']['run-id']==38305592967
    assert d['with']['name']=='gds-electrical-incremental-route-38305592967'
    code=next(s['run'] for s in steps if s['name']=='Validate artifact and repaired netlist')
    assert 'validate_electrical' in code and "os.environ['REVIEWED_NETLIST_SHA']" in code

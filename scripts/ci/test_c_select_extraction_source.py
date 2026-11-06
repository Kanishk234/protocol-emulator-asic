import pytest
import hashlib
import json
from pathlib import Path

from c_select_extraction_source import require_completion, validate


def fixture():
    return dict(detailed_routing_completed=True,disconnected_pin_checker_passed=True,
                route_drc_errors=0,antenna_violating_nets=0,source_run=42156980762,
                extracted_timing_performed=False,official_gds_qualified=False)


def test_completed_route_accepts():
    require_completion(fixture())


@pytest.mark.parametrize('key,value', [('detailed_routing_completed',False),
    ('disconnected_pin_checker_passed',False),('route_drc_errors',1),
    ('route_drc_errors',False),('antenna_violating_nets',1),('source_run',0),
    ('extracted_timing_performed',True),('official_gds_qualified',True)])
def test_partial_or_different_route_rejects(key,value):
    receipt=fixture();receipt[key]=value
    with pytest.raises(AssertionError):
        require_completion(receipt)


@pytest.mark.parametrize('fault', [None, 'hash', 'provenance', 'critical_pin', 'view'])
def test_exact_routed_input_validation(tmp_path,monkeypatch,fault):
    monkeypatch.chdir(tmp_path)
    root=Path('artifact');stage=Path('runs/c-select-pass-route/1-openroad-detailedrouting')
    (root/stage).mkdir(parents=True)
    state={'metrics':{'route__drc_errors':0}}
    for key,suffix in (('odb','odb'),('def','def'),('nl','nl.v'),('pnl','pnl.v'),('sdc','sdc')):
        name=stage/('tt_um_tripwire.'+suffix)
        (root/name).write_text(key);state[key]=str(Path.cwd()/name)
    if fault=='view':state['odb']='/wrong.odb'
    source=str(stage/'state_out.json')
    (root/source).write_text(json.dumps(state))
    completion=fixture();completion['state']=source
    (root/'runs/c-select-pass-route/completion.json').write_text(json.dumps(completion))
    (root/'antenna.json').write_text(json.dumps({'antenna__violating__nets':0,'antenna__violating__pins':0}))
    (root/'pins.json').write_text(json.dumps({'design__critical_disconnected_pin__count':1 if fault=='critical_pin' else 0,'design__disconnected_pin__count':1}))
    manifest=dict(run={'id':1},artifact={'id':2},source_state=source,antenna_metrics='antenna.json',
                  disconnected_metrics='pins.json',noncritical_disconnected_pins=1,files={
                      str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in root.rglob('*') if p.is_file()})
    if fault=='hash':(root/source).write_text('changed')
    if fault:
        with pytest.raises(AssertionError):
            validate(root,manifest,{'id':0 if fault=='provenance' else 1},{'id':2})
    else:assert validate(root,manifest,{'id':1},{'id':2})==(root/source).resolve()

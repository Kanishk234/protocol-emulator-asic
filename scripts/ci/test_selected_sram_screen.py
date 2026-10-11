import hashlib
from pathlib import Path
import pytest
import selected_sram_plan as plan
import selected_sram_screen as runner


def source(monkeypatch):
    nl='sg13cmos5l_buf_4 wire9447 (.A(\\u_chip.g_lane[0].u_lane.mem_rdata[0] ), .X(net9447));'
    layout='- wire9447 sg13cmos5l_buf_4 + PLACED ( 473760 230580 ) N ;'
    monkeypatch.setattr(plan,'NL_SHA',hashlib.sha256(nl.encode()).hexdigest())
    monkeypatch.setattr(plan,'DEF_SHA',hashlib.sha256(layout.encode()).hexdigest())
    return nl,layout


def test_exact_unchanged_cell_move(monkeypatch):
    nl,layout=source(monkeypatch);p=plan.plan(nl,layout,'relocate')
    plan.validate_change(nl,layout,nl,p)
    assert p['relocated_instances']==1 and p['added_buffers']==0
    plan.verify_location(layout.replace('473760 230580','25920 245700'))
    with pytest.raises(ValueError):plan.verify_location(layout)


@pytest.mark.parametrize('change',['source','layout','wire','master','proposal'])
def test_rejects_unreviewed_changes(monkeypatch,change):
    nl,layout=source(monkeypatch);p=plan.plan(nl,layout,'relocate');after=nl
    if change=='source':nl+='changed'
    if change=='layout':layout+='changed'
    if change=='wire':after=after.replace('net9447','other')
    if change=='master':after=after.replace('buf_4','buf_8')
    if change=='proposal':p['new_location'][0]=0
    with pytest.raises(ValueError):plan.validate_change(nl,layout,after,p)


@pytest.mark.parametrize('key,value',[('id',1),('head_sha','wrong'),('head_branch','other'),('conclusion','failure'),('path','wrong')])
def test_wrong_provenance_before_read(tmp_path,key,value):
    run=dict(id=runner.SOURCE_RUN,head_sha=runner.SOURCE_SHA,head_branch='main',conclusion='success',path='.github/workflows/gds-fanout-setup-route.yaml')
    run[key]=value
    with pytest.raises(ValueError,match='provenance'):runner.validate_inputs(tmp_path,run,{},{})


def test_workflow_exact_source():
    import yaml
    root=Path(__file__).resolve().parents[2]
    w=yaml.safe_load((root/'.github/workflows/gds-selected-sram-screen.yaml').read_text())
    steps=w['jobs']['harden']['steps'];d=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert d['with']['run-id']==38108912678
    assert d['with']['name']=='gds-fanout-setup-route-38108912678'
    assert any('selected_sram_screen.py --kind relocate' in s.get('run','') for s in steps)


@pytest.mark.parametrize('displaced',[False,True])
def test_promote_requires_destination_and_fresh_views(tmp_path,monkeypatch,displaced):
    import json
    nl,layout=source(monkeypatch);proposal=plan.plan(nl,layout,'relocate')
    baseline=tmp_path/'source.v';baseline.write_text(nl)
    original=tmp_path/'source.def';original.write_text(layout)
    placed=tmp_path/'moved.def';placed.write_text(layout if displaced else layout.replace('473760 230580','25920 245700'))
    odb=tmp_path/'chip.odb'
    for suffix in ['.baseline.nl.v','.eco.nl.v','.eco.pnl.v']:odb.with_suffix(suffix).write_text(nl)
    state=tmp_path/'state_out.json';state.write_text(json.dumps(dict(odb=str(odb),def_=str(placed),spef='stale',sdf='stale',lib='stale')))
    data=json.loads(state.read_text());data['def']=data.pop('def_');state.write_text(json.dumps(data))
    if displaced:
        with pytest.raises(ValueError,match='destination'):runner.promote(state,baseline,original,proposal)
    else:
        data=json.loads(runner.promote(state,baseline,original,proposal).read_text())
        assert data['spef'] is data['sdf'] is data['lib'] is None

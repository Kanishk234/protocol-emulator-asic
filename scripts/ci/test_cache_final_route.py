import copy
from pathlib import Path
import subprocess

import pytest
import yaml

import cache_final_route as trial
from postgrt_timing import CORNERS

ROOT=Path(__file__).resolve().parents[2]


def test_only_exact_successful_screen_is_admitted():
    good=dict(id=trial.SOURCE_RUN,head_sha=trial.SOURCE_SHA,head_branch='main',conclusion='success',path=trial.SOURCE_WORKFLOW)
    trial.validate_metadata(good)
    for k in good:
        with pytest.raises(ValueError):trial.validate_metadata({**good,k:'wrong'})


def test_saved_paths_are_contained_and_absolute_runner_paths_are_mapped(tmp_path):
    p=tmp_path/'runs/source.odb';p.parent.mkdir();p.write_text('db')
    assert trial.local_view(tmp_path,str(trial.RUNNER_ROOT/'runs/source.odb'))==p
    assert trial.local_view(tmp_path,'runs/source.odb')==p
    for bad in ('/etc/passwd','../source.odb','missing.odb'):
        with pytest.raises(ValueError):trial.local_view(tmp_path,bad)


def evidence():
    summary={}
    functional={}
    electrical={}
    for c in CORNERS:
        summary.update({f'timing__setup__ws__corner:{c}':0,f'timing__hold__ws__corner:{c}':.1,
                        f'timing__setup_vio__count__corner:{c}':0,f'timing__hold_vio__count__corner:{c}':0})
        functional[c]={'worst_reported_setup_slack_ns':1.25}
        electrical[c]={'no_reported_electrical_violations':True}
    return summary,functional,electrical,{'antenna__violating__nets':0,'antenna__violating__pins':0}


def test_actual_positive_reserve_is_required_beside_nonnegative_ordinary_checks():
    assert not trial.extracted_failures(*evidence())


@pytest.mark.parametrize('case',['negative_setup','zero_functional','negative_functional','fast_hold','bad_hold','missing_corner','electrical','antenna','bool_antenna','timing_count'])
def test_extracted_failures_cannot_be_hidden_by_a_green_route(case):
    summary,func,electrical,antenna=evidence()
    c=CORNERS[0]
    if case=='negative_setup':summary[f'timing__setup__ws__corner:{c}']=-.01
    if case=='zero_functional':func[c]['worst_reported_setup_slack_ns']=0
    if case=='negative_functional':func[c]['worst_reported_setup_slack_ns']=-.01
    if case=='fast_hold':summary[f'timing__hold__ws__corner:{c}']=.049999
    if case=='bad_hold':summary[f'timing__hold__ws__corner:{c}']=float('nan')
    if case=='missing_corner':func.pop(c)
    if case=='electrical':electrical[c]['no_reported_electrical_violations']=False
    if case=='antenna':antenna['antenna__violating__nets']=1
    if case=='timing_count':summary[f'timing__setup_vio__count__corner:{c}']=1
    if case=='bool_antenna':antenna['antenna__violating__pins']=False
    assert trial.extracted_failures(summary,func,electrical,antenna)


def test_workflow_is_manual_source_bound_and_extraction_depends_on_clean_route():
    w=yaml.safe_load((ROOT/'.github/workflows/gds-cache-final-route-extracted.yaml').read_text())
    assert w['on']=={'workflow_dispatch':{}}
    assert w['jobs']['extraction']['needs']=='route'
    assert 'if' not in w['jobs']['extraction']
    for job in w['jobs'].values():
        assert job['env']['SOURCE_RUN']==str(trial.SOURCE_RUN)
        assert job['env']['SOURCE_ARTIFACT']=='official-dev4-cache-final-antenna-44017640255'
        text='\n'.join(s.get('run','') for s in job['steps'])
        assert trial.SOURCE_SHA in text
        assert "run['conclusion'] == 'success'" in text
        assert trial.SOURCE_WORKFLOW in text
        assert 'dcf36133a369abc8f3c5e5738cd4d82e4903c0e0' in text
        assert 'approved_initial_antenna_exception' not in text
        for step in job['steps']:
            if 'run' in step:subprocess.run(['bash','-n'],input=step['run'],text=True,check=True)
    source=(ROOT/'scripts/ci/cache_final_route.py').read_text()
    assert 'run_extract(ROUTE,stock_constraints=True,functional_setup=True)' in source
    assert "run_step(config,source,ROUTE,['OpenROAD.DetailedRouting'])" in source


def test_extracted_report_cannot_drop_previously_timed_endpoints():
    summary,func,electrical,antenna=evidence()
    for c in CORNERS:func[c]['endpoint_inventory']={'FLOP_DATA_ENDPOINTS':2418,'OUTPUT_ENDPOINTS':24}
    expected={c:dict(r['endpoint_inventory']) for c,r in func.items()}
    assert not trial.extracted_failures(summary,func,electrical,antenna,expected)
    func[CORNERS[0]]['endpoint_inventory']['FLOP_DATA_ENDPOINTS']=1
    assert trial.extracted_failures(summary,func,electrical,antenna,expected)


@pytest.mark.parametrize('raw_drc,passes',[(0,True),(1,False),(False,False),(None,False)])
def test_route_requires_fresh_drc_zero_not_an_inherited_zero(tmp_path,monkeypatch,raw_drc,passes):
    import json
    monkeypatch.chdir(tmp_path);monkeypatch.setenv('GITHUB_RUN_ID','123')
    monkeypatch.setattr(trial,'verify_source',lambda:(Path('source.json'),{}))
    monkeypatch.setattr(trial,'restore_pdk',lambda row:None)
    monkeypatch.setattr(trial,'validate_final_route',lambda *args:None)
    (tmp_path/'runs').mkdir()
    (tmp_path/'runs/cache-final-pre-route-gates.json').write_text(json.dumps(dict(qualified=True,source_run=trial.SOURCE_RUN,source_sha=trial.SOURCE_SHA,source_odb_sha256=trial.ODB_SHA,workflow_run_id='123')))
    def run_step(*args):
        stage=trial.ROUTE/'1-openroad-detailedrouting';stage.mkdir(parents=True)
        p=stage/'chip.v';p.write_text('routed view')
        state=dict(metrics={'route__drc_errors':0},odb=str(p),nl=str(p))
        (stage/'state_out.json').write_text(json.dumps(state))
        (stage/'or_metrics_out.json').write_text(json.dumps({'route__drc_errors':raw_drc}))
    monkeypatch.setattr(trial,'run_step',run_step)
    if passes:
        trial.route();assert (trial.ROUTE/'route_completion.json').is_file()
    else:
        with pytest.raises(ValueError,match='fresh DRC0'):trial.route()
        assert not (trial.ROUTE/'route_completion.json').exists()

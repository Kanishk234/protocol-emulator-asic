import json
import pytest
from pathlib import Path
import extracted_sizing_sensitivity as runner
from event_nor2_screen import logical_cells
from native_stock_route import CORNERS


def netlist():
    return '\n'.join(f'{old} {name} (.A(a), .X(x));' for name,(old,new) in runner.TARGETS.items())+'\nsg13cmos5l_buf_1 unrelated (.A(in), .X(out));'


@pytest.mark.parametrize('case',list(runner.CASES))
def test_only_reviewed_masters_change_and_all_connections_retained(case):
    text=netlist();old=logical_cells(text);changes=runner.CASES[case]
    new=logical_cells(runner.change_netlist(text,changes))
    assert set(new)==set(old)
    for n,(master,pins) in new.items():assert (master,pins)==(changes.get(n,old[n][0]),old[n][1])


@pytest.mark.parametrize('fault',['master','missing','duplicate','unknown','wrong_variant'])
def test_changed_source_and_unreviewed_targets_refused(fault):
    text=netlist();changes={'place7221':'sg13cmos5l_buf_2'}
    if fault=='master':text=text.replace('sg13cmos5l_buf_1 place7221','sg13cmos5l_buf_4 place7221')
    if fault=='missing':text=text.replace('place7221','missing')
    if fault=='duplicate':text+='\nsg13cmos5l_buf_1 place7221 (.A(a), .X(x));'
    if fault=='unknown':changes={'unrelated':'sg13cmos5l_buf_2'}
    if fault=='wrong_variant':changes={'place7221':'sg13cmos5l_inv_2'}
    with pytest.raises(ValueError):runner.change_netlist(text,changes)


@pytest.mark.parametrize('fault',[None,'regression','nan','missing'])
def test_baseline_must_reproduce_actual_extraction(fault):
    reference={f'timing__{kind}__ws__corner:{c}':.05 if kind=='hold' else -1 for c in CORNERS for kind in ('setup','hold')}
    metrics={c:dict(reference) for c in CORNERS};key=f'timing__setup__ws__corner:{CORNERS[0]}'
    if fault=='regression':metrics[CORNERS[0]][key]=0
    if fault=='nan':metrics[CORNERS[0]][key]=float('nan')
    if fault=='missing':metrics[CORNERS[0]].pop(key)
    if fault:
        with pytest.raises((ValueError,KeyError)):runner.baseline_matches(metrics,reference)
    else:runner.baseline_matches(metrics,reference)


def test_exact_failed_route_is_deliberately_diagnostic_only():
    run=dict(id=runner.SOURCE_RUN,head_sha=runner.SOURCE_SHA,head_branch='main',conclusion='failure',path='.github/workflows/gds-electrical-incremental-route.yaml')
    runner.validate_run(run)
    for field,value in [('id',1),('head_sha','wrong'),('conclusion','success')]:
        with pytest.raises(ValueError):runner.validate_run(dict(run,**{field:value}))


def test_workflow_downloads_exact_route_and_launches_only_sensitivity():
    import yaml
    root=Path(__file__).resolve().parents[2]
    p=root/'.github/workflows/gds-extracted-sizing-sensitivity.yaml';w=yaml.safe_load(p.read_text())
    steps=w['jobs']['harden']['steps'];d=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert d['with']['run-id']==runner.SOURCE_RUN and d['with']['name']==f'gds-electrical-incremental-route-{runner.SOURCE_RUN}'
    launch=next(s['run'] for s in steps if 'extracted_sizing_sensitivity.py' in s.get('run',''))
    assert launch=='python workflow-src/scripts/ci/extracted_sizing_sensitivity.py'
    code=(root/'scripts/ci/extracted_sizing_sensitivity.py').read_text()
    assert "['OpenROAD.STAPostPNR']" in code and 'OpenROAD.DetailedRouting' not in code
    assert 'physical_qualified=False' in code and 'fixed_spef=True' in code

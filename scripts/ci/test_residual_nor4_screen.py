import copy
import hashlib
import json
from pathlib import Path
import pytest
import residual_nor4_plan as plan
import residual_nor4_screen as runner


def source(monkeypatch):
    before = 'sg13cmos5l_nor4_1 _25245_ (.A(net7308), .B(b), .C(c), .D(d), .Y(net7307));'
    layout = '- _25245_ sg13cmos5l_nor4_1 + PLACED ( 100 100 ) N ;'
    monkeypatch.setattr(plan, 'NL_SHA', hashlib.sha256(before.encode()).hexdigest())
    monkeypatch.setattr(plan, 'DEF_SHA', hashlib.sha256(layout.encode()).hexdigest())
    return before, layout


def test_exact_single_strength_change(monkeypatch):
    before, layout = source(monkeypatch)
    p = plan.plan(before, layout, 'setup')
    plan.validate_change(before, layout, before.replace('nor4_1', 'nor4_2'), p)
    assert p['added_buffers'] == 0 and p['changed_cells'] == 1
    assert 'sg13cmos5l_nor4_2' in plan.target_call(before, layout, 'setup')


@pytest.mark.parametrize('bad', ['source', 'layout', 'wire', 'master', 'proposal'])
def test_unreviewed_changes_fail(monkeypatch, bad):
    before, layout = source(monkeypatch)
    p = plan.plan(before, layout, 'setup')
    after = before.replace('nor4_1', 'nor4_2')
    if bad == 'source': before += ' changed'
    if bad == 'layout': layout += ' changed'
    if bad == 'wire': after = after.replace('net7308', 'other')
    if bad == 'master': after = after.replace('nor4_2', 'inv_4')
    if bad == 'proposal': p['new_master'] = 'sg13cmos5l_buf_8'
    with pytest.raises(ValueError): plan.validate_change(before, layout, after, p)


def test_workflow_pins_selected_extracted_source():
    import yaml
    root = Path(__file__).resolve().parents[2]
    workflow = yaml.safe_load((root/'.github/workflows/gds-residual-nor4-screen.yaml').read_text())
    steps = workflow['jobs']['harden']['steps']
    download = next(s for s in steps if 'download-artifact@' in s.get('uses', ''))
    assert download['with']['run-id'] == 38116800326
    assert download['with']['name'] == 'gds-dominant-slew-route-38116800326'
    assert any('residual_nor4_screen.py --kind setup' in s.get('run', '') for s in steps)


def test_promote_validates_master_and_removes_stale_parasitics(tmp_path, monkeypatch):
    before, layout = source(monkeypatch)
    p = plan.plan(before, layout, 'setup')
    baseline = tmp_path/'baseline.v'; baseline.write_text(before)
    physical = tmp_path/'chip.def'; physical.write_text(layout)
    odb = tmp_path/'chip.odb'
    odb.with_suffix('.baseline.nl.v').write_text(before)
    for suffix in ['.eco.nl.v', '.eco.pnl.v']:
        odb.with_suffix(suffix).write_text(before.replace('nor4_1', 'nor4_2'))
    state = tmp_path/'state_out.json';state.write_text(json.dumps(dict(odb=str(odb),spef='old',sdf='old',lib='old')))
    fresh = json.loads(runner.promote(state, baseline, physical, p).read_text())
    assert fresh['spef'] is fresh['sdf'] is fresh['lib'] is None


@pytest.mark.parametrize('key,value', [('id',1),('head_sha','wrong'),('head_branch','other'),('conclusion','failure'),('path','wrong')])
def test_wrong_source_provenance_fails_before_artifact_read(tmp_path, key, value):
    run = dict(id=runner.SOURCE_RUN, head_sha=runner.SOURCE_SHA, head_branch='main',
               conclusion='success', path='.github/workflows/gds-dominant-slew-route.yaml')
    run[key] = value
    with pytest.raises(ValueError, match='provenance'):
        runner.validate_inputs(tmp_path, run, {}, {})

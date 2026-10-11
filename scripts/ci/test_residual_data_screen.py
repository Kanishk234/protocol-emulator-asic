import json
from pathlib import Path
import pytest
import residual_data_screen as runner
import residual_data_plan as planner
from test_residual_data_plan import fixture, changed


@pytest.mark.parametrize('key,value', [('id', 1), ('head_sha', 'wrong'),
    ('head_branch', 'other'), ('conclusion', 'failure'), ('path', 'wrong')])
def test_wrong_provenance_before_read(tmp_path, key, value):
    run = dict(id=runner.SOURCE_RUN, head_sha=runner.SOURCE_SHA, head_branch='main',
               conclusion='success', path='.github/workflows/gds-retained-sram2-route.yaml')
    run[key] = value
    with pytest.raises(ValueError, match='provenance'):
        runner.validate_inputs(tmp_path, run, {}, {})


def test_workflow_uses_exact_measured_source_and_one_net():
    import yaml
    root = Path(__file__).resolve().parents[2]
    w = yaml.safe_load((root/'.github/workflows/gds-residual-data-screen.yaml').read_text())
    steps = w['jobs']['harden']['steps']
    d = next(s for s in steps if 'download-artifact@' in s.get('uses', ''))
    assert d['with']['run-id'] == runner.SOURCE_RUN
    assert d['with']['name'] == 'gds-retained-sram2-route-38172640071'
    assert any('residual_data_screen.py --kind _28820_' in s.get('run', '') for s in steps)


@pytest.mark.parametrize('rewire', [False, True])
def test_promote_validates_complete_partition_and_clears_stale_parasitics(tmp_path, monkeypatch, rewire):
    nl, layout = fixture(monkeypatch)
    proposal = planner.plan(nl, layout, '_28807_')
    after = changed(nl, proposal)
    if rewire:
        after = after.replace('.A(a)', '.A(other)')
    baseline = tmp_path/'before.v'; baseline.write_text(nl)
    original = tmp_path/'before.def'; original.write_text(layout)
    odb = tmp_path/'chip.odb'
    odb.with_suffix('.baseline.nl.v').write_text(nl)
    for suffix in ('.eco.nl.v', '.eco.pnl.v'):
        odb.with_suffix(suffix).write_text(after)
    state = tmp_path/'state_out.json'
    state.write_text(json.dumps(dict(odb=str(odb), spef='old', sdf='old', lib='old')))
    if rewire:
        with pytest.raises(ValueError): runner.promote(state, baseline, original, proposal)
    else:
        result = json.loads(runner.promote(state, baseline, original, proposal).read_text())
        assert result['spef'] is result['sdf'] is result['lib'] is None

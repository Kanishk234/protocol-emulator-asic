import copy
from pathlib import Path
import pytest
from combined_physical_route import validate_provenance
from route_reserve_route import PROFILE
from route_reserve_plan import BINDING


@pytest.mark.parametrize('key,value', [('qualified', False), ('fanout_reserve_pass', False),
    ('internal_maximum_loads', 8), ('added_buffers', 18), ('post_antenna_buffers', 0)])
def test_changed_gate_receipt_refused(key, value):
    gates = copy.deepcopy(PROFILE['gate_receipt'])
    gates[key] = value
    with pytest.raises(ValueError):
        validate_provenance(PROFILE['run_binding'], gates, PROFILE)


def test_exact_source_and_reserved_families():
    validate_provenance(PROFILE['run_binding'], PROFILE['gate_receipt'], PROFILE)
    assert PROFILE['source_run'] == 38687129808
    assert PROFILE['gate_receipt']['source_run'] == BINDING['source_run'] == 38679335674
    assert max(PROFILE['gate_receipt']['loads'].values()) == 4
    assert len(PROFILE['gate_receipt']['loads']) == 26


def test_workflow_continues_exact_screen_without_another_full_grt():
    import yaml
    root = Path(__file__).resolve().parents[2]
    w = yaml.safe_load((root/'.github/workflows/gds-route-reserve-route.yaml').read_text())
    steps = w['jobs']['harden']['steps']
    d = next(s for s in steps if 'download-artifact@' in s.get('uses', ''))
    assert d['with']['run-id'] == 38687129808
    assert d['with']['name'] == 'gds-route-reserve-screen-38687129808'
    assert any(s.get('run') == 'python workflow-src/scripts/ci/route_reserve_route.py' for s in steps)
    assert not any('GlobalRouting' in s.get('run', '') or 'docker build' in s.get('run', '') for s in steps)
    summary = next(s for s in steps if 'upload-artifact@' in s.get('uses', ''))
    assert summary['if'] == "always() && hashFiles('runs/route-reserve-route/extracted_gates.json') != ''"

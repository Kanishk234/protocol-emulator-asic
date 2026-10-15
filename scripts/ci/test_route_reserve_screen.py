from pathlib import Path
import pytest
from route_reserve_gate import measure
from route_reserve_plan import BINDING, plan
from route_reserve_screen import PROFILE


def test_source_binding_and_strict_screen():
    assert BINDING['source_run'] == PROFILE['source_run'] == 38679335674
    assert BINDING['electrical_nets'] == 7
    assert BINDING['hold_count'] == 0
    assert PROFILE['run_binding']['head_sha'] == 'b049a17343b3ff9912f596aa9953be1397c5baf7'
    with pytest.raises(ValueError, match='Wrong combined source'):
        plan('wrong', 'wrong', 'wrong', {}, Path('absent'), Path('absent'))


def test_reserve_rejects_legal_but_fragile_seven_load_net():
    proposal = {'groups': [{'source_net': 'n', 'net': 'branch'}]}
    text = '\nNETS 2 ;\n- n ( driver X ) ( branch_driver A ) ;\n- branch ( branch_driver X ) '
    text += ' '.join(f'( sink{i} A )' for i in range(7)) + ' ;\nEND NETS\n'
    result = measure(text, proposal)
    assert result['loads']['branch'] == 7
    assert result['fanout_reserve_pass'] is False
    assert measure(text.replace('( sink6 A )', ''), proposal)['fanout_reserve_pass'] is True


def test_workflow_is_screen_only_and_uses_completed_route():
    import yaml
    root = Path(__file__).resolve().parents[2]
    w = yaml.safe_load((root/'.github/workflows/gds-route-reserve-screen.yaml').read_text())
    steps = w['jobs']['harden']['steps']
    download = next(s for s in steps if 'download-artifact@' in s.get('uses', ''))
    assert download['with']['run-id'] == 38679335674
    assert download['with']['name'] == 'gds-fanout-slew-route-38679335674'
    assert any(s.get('run') == 'python workflow-src/scripts/ci/route_reserve_screen.py' for s in steps)
    assert 'detailedrouting' not in str(w).lower()

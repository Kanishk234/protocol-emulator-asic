from pathlib import Path

import pytest

from banked_sram_hold_route import REPAIR_RUN, SOURCE_RUN, VARIANT, CORNERS, validate_gate, validate_repair_run


@pytest.mark.parametrize('failure', [None, 'id', 'argument', 'branch', 'path', 'conclusion'])
def test_repair_provenance_is_exact(failure):
    run = {'id': REPAIR_RUN, 'head_branch': 'main', 'conclusion': 'success',
           'path': '.github/workflows/gds-banked-sram-hold-screen.yaml'}
    selected = REPAIR_RUN
    if failure == 'id': run['id'] += 1
    if failure == 'argument': selected += 1
    if failure == 'branch': run['head_branch'] = 'other'
    if failure == 'path': run['path'] = '.github/workflows/gds-placement-route.yaml'
    if failure == 'conclusion': run['conclusion'] = 'failure'
    if failure:
        with pytest.raises(ValueError): validate_repair_run(run, selected)
    else:
        validate_repair_run(run, selected)


@pytest.mark.parametrize('failure', [None, 'screen-id', 'variant', 'ready', 'drt', 'state', 'timing-state',
                                    'fast-budget', 'hold-count', 'slow-setup', 'antenna'])
def test_saved_repair_requires_matching_state_and_all_gates(failure):
    source = Path('saved-state.json')
    gates = {'source_run_id': SOURCE_RUN, 'variant': VARIANT, 'ready_for_route_review': True,
             'drt_launched': False, 'state': str(source)}
    timing = {'after_state': str(source)}
    timing['corners'] = {c: {'after': {**{f'timing__{k}__ws__corner:{c}': 0.07 if k == 'hold' else 0 for k in ('setup', 'hold')},
                                     **{f'timing__{k}_vio__count__corner:{c}': 0 for k in ('setup', 'hold')}}} for c in CORNERS}
    antenna = {'antenna__violating__nets': 0, 'antenna__violating__pins': 0}
    if failure == 'screen-id': gates['source_run_id'] += 1
    if failure == 'variant': gates['variant'] = 'bs-event-late'
    if failure == 'ready': gates['ready_for_route_review'] = False
    if failure == 'drt': gates['drt_launched'] = True
    if failure == 'state': gates['state'] = 'another.json'
    if failure == 'timing-state': timing['after_state'] = 'another.json'
    if failure == 'fast-budget': timing['corners'][CORNERS[0]]['after'][f'timing__hold__ws__corner:{CORNERS[0]}'] = 0.049
    if failure == 'hold-count': timing['corners'][CORNERS[0]]['after'][f'timing__hold_vio__count__corner:{CORNERS[0]}'] = 1
    if failure == 'slow-setup': timing['corners'][CORNERS[1]]['after'][f'timing__setup__ws__corner:{CORNERS[1]}'] = -0.001
    if failure == 'antenna': antenna['antenna__violating__nets'] = 1
    if failure:
        with pytest.raises(ValueError): validate_gate(gates, timing, antenna, source)
    else:
        validate_gate(gates, timing, antenna, source)


def test_original_banked_screen_cannot_route_directly(monkeypatch):
    import placement_route
    monkeypatch.setenv('SOURCE_VARIANT', VARIANT)
    monkeypatch.delenv('REPAIRED_SOURCE_RUN_ID', raising=False)
    with pytest.raises(ValueError, match='requires the reviewed repaired source'):
        placement_route.main()


def test_repaired_branch_delegates_before_original_failed_source_is_read(monkeypatch):
    import placement_route
    import banked_sram_hold_route
    monkeypatch.setenv('REPAIRED_SOURCE_RUN_ID', str(REPAIR_RUN))
    monkeypatch.setattr(banked_sram_hold_route, 'main', lambda: 'guarded repaired route')
    assert placement_route.main() == 'guarded repaired route'


def test_route_workflow_downloads_repair_artifact_without_repeating_headroom():
    import yaml
    p = Path(__file__).resolve().parents[2] / '.github/workflows/gds-placement-route.yaml'
    w = yaml.load(p.read_text(), Loader=yaml.BaseLoader)
    inputs = w['on']['workflow_dispatch']['inputs']
    assert 'bs-event-pin-banked' in inputs['source_variant']['options']
    assert inputs['repaired_source_run_id']['default'] == ''
    steps = w['jobs']['harden']['steps']
    downloads = [s for s in steps if s.get('uses', '').startswith('actions/download-artifact@')]
    assert len(downloads) == 2
    assert downloads[0]['if'] == "inputs.repaired_source_run_id == ''"
    assert downloads[1]['if'] == "inputs.repaired_source_run_id != ''"
    assert downloads[1]['with']['name'] == 'gds-banked-sram-hold-${{ inputs.repaired_source_run_id }}'
    assert any('placement-repaired-run.json' in s.get('run', '') for s in steps)

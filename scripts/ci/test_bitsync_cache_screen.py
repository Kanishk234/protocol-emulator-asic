"""Preserve the reviewed stock physical flow and all its acceptance gates."""
from pathlib import Path

import yaml


def test_cache_screen_preserves_every_stock_measurement_and_gate():
    root = Path(__file__).resolve().parents[2]
    reference = yaml.safe_load((root / '.github/workflows/gds-official-dev4-hold125-screen.yaml').read_text())
    trial = yaml.safe_load((root / '.github/workflows/tripwire-bitsync-cache-screen.yaml').read_text())
    old = reference['jobs']['screen']
    new = trial['jobs']['screen']
    assert new['strategy'] == old['strategy']
    assert new['env'] == old['env']
    assert new['timeout-minutes'] == old['timeout-minutes']
    by_name = {step.get('name'): step for step in new['steps']}
    assert len(by_name) == len(new['steps'])
    for step in old['steps']:
        actual = by_name[step.get('name')]
        if 'run' in step:
            assert actual['run'] == 'source .venv/bin/activate\n' + step['run']
        elif 'upload-artifact' not in step.get('uses', ''):
            assert actual == step
    names = [step.get('name') for step in new['steps']]
    assert names.index('Require exact cache-trial cloud success') < names.index(
        'Prepare the full design with strict stock project inputs')
    assert names.index('Apply only the bound bitsync cache storage change') < names.index(
        'Select only the comparison tile size')
    assert trial['on']['workflow_dispatch'] == {}
    assert trial['on']['push'] == dict(branches=['tripwire/closure-8x4'],
        paths=['.github/workflows/tripwire-bitsync-cache-screen.yaml'])

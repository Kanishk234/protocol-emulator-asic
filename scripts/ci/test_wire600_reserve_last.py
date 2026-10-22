import ast
from pathlib import Path
import subprocess

import pytest
import yaml

import wire600_reserve_finish as prior
import wire600_reserve_last as trial


def test_one_additional_source_and_no_new_resizes():
    old, new = prior.REVIEW, trial.REVIEW
    assert set(new['extra_sources']) - set(old['extra_sources']) == {'_11520_'}
    assert list(new['extra_sources']) == [*old['extra_sources'], '_11520_']
    assert {k: new['extra_sources'][k] for k in old['extra_sources']} == old['extra_sources']
    assert new['resizes'] == old['resizes']
    assert new['extra_sources']['_11520_'] == {
        'driver': ['_37574_', 'Y'], 'terms': [['_37574_', 'Y'], ['_37575_', 'B1']]}
    assert new['evidence_run'] == 39700222717
    assert new['proposal_sha256'] != old['proposal_sha256']


def test_profile_passes_frozen_review_to_all_audits(monkeypatch):
    assert all(f.keywords == {'review': trial.REVIEW} for f in
               (trial.plan, trial.target_call, trial.validate_change))
    calls = []
    monkeypatch.setattr(trial, 'screen', lambda **kw: calls.append(kw))
    trial.main()
    assert calls == [dict(plan_builder=trial.plan, target_emitter=trial.target_call,
                          connectivity_audit=trial.validate_change,
                          output=Path('runs/wire600-reserve-last-screen'))]
    with pytest.raises(ValueError, match='Unreviewed'):
        trial.target_call('wrong source', {'groups': [], 'resizes': []})


def test_workflow_keeps_original_source_and_all_gate_inputs():
    root = Path(__file__).resolve().parents[2]
    old = yaml.safe_load((root/'.github/workflows/gds-wire600-reserve-finish-screen.yaml').read_text())['jobs']['harden']
    new = yaml.safe_load((root/'.github/workflows/gds-wire600-reserve-last-screen.yaml').read_text())['jobs']['harden']
    assert old['env'] == new['env']
    assert old['strategy'] == new['strategy']
    download = next(s for s in new['steps'] if s['name'] == 'Download exact failed wire600 checkpoint')
    assert download['with']['run-id'] == 39677316308
    text = '\n'.join(s.get('run', '') for s in new['steps'])
    assert 'wire600_reserve_last.py' in text
    assert "final < ids.index('OpenROAD.DetailedRouting')" in text
    for step in new['steps']:
        if 'run' not in step:
            continue
        s = step['run']
        subprocess.run(['bash', '-n'], input=s, text=True, check=True)
        if "<<'PY'\n" in s:
            ast.parse(s.split("<<'PY'\n", 1)[1].split('\nPY', 1)[0])

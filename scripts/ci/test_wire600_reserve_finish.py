import copy
from pathlib import Path

import pytest
import yaml

from event_nor2_screen import logical_cells
import wire600_reserve_finish as trial


def reference():
    lines = ['module example;']
    for r in trial.REVIEW['resizes']:
        pins = []
        for p, n in r['pins'].items():
            value = '\\'+n+' ' if '[' in n or '.' in n else n
            pins.append('.'+p+'('+value+')')
        lines.append(r['old_master']+' '+r['instance']+' ('+', '.join(pins)+');')
    lines.append('sg13cmos5l_buf_1 unchanged (.A(a), .X(b));')
    lines.append('endmodule')
    return '\n'.join(lines)


def test_only_reviewed_masters_change_and_all_pins_stay(monkeypatch):
    monkeypatch.setattr(trial, 'validate_proposal', lambda p: None)
    proposal = {'groups': [], 'resizes': copy.deepcopy(trial.REVIEW['resizes'])}
    before = reference()
    after = trial.resized_reference(before, proposal)
    old, new = logical_cells(before), logical_cells(after)
    assert set(old) == set(new)
    for r in proposal['resizes']:
        assert old[r['instance']][0] == r['old_master']
        assert new[r['instance']] == (r['new_master'], old[r['instance']][1])
    assert old['unchanged'] == new['unchanged']
    assert trial.validate_change(before, after, proposal)
    with pytest.raises(ValueError):
        trial.validate_change(before, after.replace('.X(b)', '.X(wrong)'), proposal)


@pytest.mark.parametrize('wrong', ['master', 'pins'])
def test_wrong_resize_source_rejected(monkeypatch, wrong):
    monkeypatch.setattr(trial, 'validate_proposal', lambda p: None)
    before = reference()
    if wrong == 'master':
        before = before.replace('sg13cmos5l_nor3_1', 'sg13cmos5l_nand3_1')
    else:
        before = before.replace('.A(_04892_)', '.A(wrong)')
    with pytest.raises(ValueError, match='resize'):
        trial.resized_reference(before, {'groups': [], 'resizes': trial.REVIEW['resizes']})


def test_noncanonical_proposal_cannot_reach_emitter():
    with pytest.raises(ValueError, match='Unreviewed'):
        trial.target_call('untrusted source', {'groups': [], 'resizes': []})


def test_profile_reuses_strict_runner(monkeypatch):
    calls = []
    monkeypatch.setattr(trial, 'screen', lambda **kw: calls.append(kw))
    trial.main()
    assert calls == [dict(plan_builder=trial.plan, target_emitter=trial.target_call,
                          connectivity_audit=trial.validate_change,
                          output=Path('runs/wire600-reserve-finish-screen'))]


def test_workflow_keeps_original_source_and_gate_environment():
    root = Path(__file__).resolve().parents[2]
    old = yaml.safe_load((root/'.github/workflows/gds-wire600-selective-screen.yaml').read_text())['jobs']['harden']
    new = yaml.safe_load((root/'.github/workflows/gds-wire600-reserve-finish-screen.yaml').read_text())['jobs']['harden']
    assert new['env'] == old['env']
    assert new['strategy'] == old['strategy']
    for job in (old, new):
        download = next(s for s in job['steps'] if s['name'] == 'Download exact failed wire600 checkpoint')
        assert download['with']['run-id'] == 39677316308
    text = '\n'.join(s.get('run', '') for s in new['steps'])
    assert 'wire600_reserve_finish.py' in text
    assert "final < ids.index('OpenROAD.DetailedRouting')" in text

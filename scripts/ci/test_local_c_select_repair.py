import copy
import json
from pathlib import Path

import pytest

from local_c_select_repair import audit_snapshot, diode_seed


def fixture():
    root = Path(__file__).resolve().parents[2]
    plan = json.loads((root / 'spikes/phase2_stock_flow/c_select_local_repair_plan.json').read_text())
    def cell(master):
        return dict(master=master, location=(100000, 100000), orientation='R0',
                    status='PLACED', pins={'A': 'a', 'X': 'b'})
    before = {'untouched': cell('original')}
    for item in plan['sizing']:
        before[item['instance']] = cell(item['original_master'])
    for item in plan['diodes']:
        before[item['anchor']] = cell(item['anchor_master'])
    after = copy.deepcopy(before)
    for item in plan['sizing']:
        after[item['instance']]['master'] = item['candidate_master']
        after[item['instance']]['location'] = (110000, 100000)
    for item in plan['diodes']:
        after[item['name']] = cell('sg13cmos5l_antennanp')
        after[item['name']]['pins'] = {'A': item['net'].replace('[', '\\[').replace(']', '\\]')}
        after[item['name']]['location'] = diode_seed(
            before[item['anchor']]['location'], item, 1000, plan['maximum_displacement_um'])
    return before, after, plan


def test_exact_bounded_intervention_accepts():
    audit_snapshot(*fixture(), 1000)


@pytest.mark.parametrize('field,value', [('location', (0, 0)), ('orientation', 'MX'),
                                       ('status', 'LOCKED'), ('master', 'changed'),
                                       ('pins', {'A': 'other'})])
def test_unrelated_mutation_rejects(field, value):
    before, after, plan = fixture()
    after['untouched'][field] = value
    with pytest.raises(AssertionError):
        audit_snapshot(before, after, plan, 1000)


def test_clock_seed_uses_reviewed_upper_corridor():
    before, after, plan = fixture()
    clock = plan['diodes'][2]
    assert clock['seed_offset_um'] == [0, 15.12]
    assert after[clock['name']]['location'] == (100000, 115120)
    after[clock['name']]['location'] = before[clock['anchor']]['location']
    with pytest.raises(AssertionError, match='reviewed corridor'):
        audit_snapshot(before, after, plan, 1000)


@pytest.mark.parametrize('offset', [[0, 21], [1], [True, 0], [0, float('nan')]])
def test_bad_seed_rejects(offset):
    with pytest.raises(ValueError):
        diode_seed((0, 0), {'seed_offset_um': offset}, 1000, 20)


@pytest.mark.parametrize('fault', ['wrong_diode_net', 'missing_diode', 'extra_cell',
                                 'diode_too_far', 'buffer_too_far', 'buffer_wrong_master',
                                 'buffer_reconnected'])
def test_intervention_drift_rejects(fault):
    before, after, plan = fixture()
    diode = plan['diodes'][2]['name']  # Explicitly protect the clock connection.
    buffer = plan['sizing'][0]['instance']
    if fault == 'wrong_diode_net': after[diode]['pins']['A'] = 'wrong_clock'
    elif fault == 'missing_diode': del after[diode]
    elif fault == 'extra_cell': after['unexpected'] = after[diode]
    elif fault == 'diode_too_far': after[diode]['location'] = (121000, 100000)
    elif fault == 'buffer_too_far': after[buffer]['location'] = (121000, 100000)
    elif fault == 'buffer_wrong_master': after[buffer]['master'] = 'other'
    elif fault == 'buffer_reconnected': after[buffer]['pins']['A'] = 'other'
    with pytest.raises(AssertionError):
        audit_snapshot(before, after, plan, 1000)

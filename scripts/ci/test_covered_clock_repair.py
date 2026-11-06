import copy
import json
from pathlib import Path

import pytest

from covered_clock_repair import DeferredClock, require_clock_preserved, split_plan


def plan():
    return json.loads((Path(__file__).resolve().parents[2] /
                       'spikes/phase2_stock_flow/c_select_covered_clock_plan.json').read_text())


def test_split_preserves_full_plan_and_excludes_clock_from_later_edit():
    source = plan()
    original = copy.deepcopy(source)
    first, second = split_plan(source)
    assert source == original
    assert first['sizing'] == [] and len(first['diodes']) == 2
    assert len(second['diodes']) == 1 and second['sizing'] == source['sizing']
    assert first['diodes'][0]['net'] not in second['allowed_signal_nets_to_reroute']
    assert len(second['allowed_signal_nets_to_reroute']) == 3
    assert '_02001_' not in second['allowed_signal_nets_to_reroute']


@pytest.mark.parametrize('fault', ['net', 'anchor', 'site', 'orientation'])
def test_unreviewed_data_protection_rejected(fault):
    source = plan()
    if fault == 'net':
        source['covered_data_nets'] = ['another']
    elif fault == 'anchor':
        source['diodes'][0]['anchor'] = 'another'
    elif fault == 'site':
        source['diodes'][0]['locked_site_dbu'][0] += 480
    else:
        source['diodes'][0]['locked_orientation'] = 'R0'
    with pytest.raises(AssertionError):
        split_plan(source)


@pytest.mark.parametrize('fault', ['reparent', 'missing', 'extra', 'location', 'orientation', 'anchor'])
def test_unreviewed_clock_plan_rejected(fault):
    source = plan()
    if fault == 'reparent':
        source['clock_reparent'] = {'instance': 'x'}
    elif fault == 'missing':
        source['diodes'].pop()
    elif fault == 'extra':
        source['diodes'].append(copy.deepcopy(source['diodes'][2]))
    elif fault == 'location':
        source['diodes'][2]['locked_site_dbu'][0] += 480
    elif fault == 'orientation':
        source['diodes'][2]['locked_orientation'] = 'R0'
    else:
        source['diodes'][2]['anchor'] = 'other'
    with pytest.raises(AssertionError):
        split_plan(source)


def test_deferred_router_rejects_data_and_power_edits():
    class Net:
        def __init__(self, name):
            self.name = name
        def getName(self):
            return self.name
    router = DeferredClock('clock[0]')
    router.addDirtyNet(Net(r'clock\[0\]'))
    for net in ('VDD', 'data', 'clock[1]'):
        with pytest.raises(AssertionError):
            router.addDirtyNet(Net(net))


def test_clock_route_must_be_identical_and_present():
    before = 'clock\n(\n0 0 Metal1 0 0 Metal3\n0 0 Metal3 10 0 Metal3\n)\n'
    require_clock_preserved(before, before, 'clock')
    for after in (before.replace('10 0', '20 0'), before.replace('clock', 'other')):
        with pytest.raises(AssertionError):
            require_clock_preserved(before, after, 'clock')

"""Preserve covered clock guides; never waive connectivity or congestion gates."""
import copy
import json
from pathlib import Path

from local_c_select_repair import apply_plan, audit_snapshot, canonical, verify_after_router
from local_antenna_repair import snapshot
from route_segment_audit import parse

PLAN = Path('spikes/phase2_stock_flow/c_select_covered_clock_plan.json')


def split_plan(plan):
    plan = copy.deepcopy(plan)
    assert not plan.get('clock_reparent'), 'Clock topology must stay unchanged'
    clocks = [d for d in plan['diodes'] if d['pin'] == 'GATE']
    assert len(clocks) == 1
    clock = clocks[0]
    assert clock['anchor'] == '_51789_' and clock['anchor_master'] == 'sg13cmos5l_dlhq_1'
    assert clock['locked_site_dbu'] == [626880, 498960]
    assert clock['locked_orientation'] == 'MX'
    covered_data = plan.get('covered_data_nets', [])
    assert covered_data in ([], ['_02001_']), 'Unreviewed covered data net'
    data = [d for d in plan['diodes'] if d['net'] in covered_data]
    assert len(data) == len(covered_data)
    if data:
        clear = data[0]
        assert (clear['anchor'], clear['anchor_master'], clear['pin']) == (
            '_46674_', 'sg13cmos5l_nor4_1', 'Y')
        assert clear['locked_site_dbu'] == [830400, 317520]
        assert clear['locked_orientation'] == 'MX'
    preserved = [clock['net']] + covered_data
    first = copy.deepcopy(plan)
    first['sizing'] = []
    first['diodes'] = [clock] + data
    first['allowed_signal_nets_to_reroute'] = preserved
    second = copy.deepcopy(plan)
    second['diodes'] = [d for d in plan['diodes'] if d['net'] not in preserved]
    second['allowed_signal_nets_to_reroute'] = [n for n in plan['allowed_signal_nets_to_reroute']
                                               if n not in preserved]
    return first, second


class DeferredClock:
    """No live router exists yet; reject any unexpected attempted net edit."""
    def __init__(self, net):
        self.nets = {net} if isinstance(net, str) else set(net)
        assert self.nets and not self.nets.intersection({'VDD', 'VSS'})

    def addDirtyNet(self, net):
        assert canonical(net.getName()) in self.nets, 'Unexpected deferred net'


def prepare(design, database):
    plan = json.loads(PLAN.read_text())
    first, second = split_plan(plan)
    before = snapshot(database.getChip().getBlock())
    receipt = apply_plan(design, DeferredClock(first['allowed_signal_nets_to_reroute']), database, first)
    verify_after_router(database, receipt)
    return dict(plan=plan, remaining=second, before=before, clock_receipt=receipt,
                units=database.getChip().getBlock().getDbUnitsPerMicron())


def apply_remaining(design, router, database, prepared):
    return apply_plan(design, router, database, prepared['remaining'])


def require_clock_preserved(before_text, after_text, net):
    before, after = parse(before_text), parse(after_text)
    old = [v for n, v in before.items() if canonical(n) == net]
    new = [v for n, v in after.items() if canonical(n) == net]
    assert len(old) == len(new) == 1 and old == new, 'Original clock route changed'


def finish(database, prepared, intervention, before_text, after_text):
    verify_after_router(database, intervention)
    audit_snapshot(prepared['before'], snapshot(database.getChip().getBlock()),
                   prepared['plan'], prepared['units'])
    clock = prepared['plan']['diodes'][2]
    require_clock_preserved(before_text, after_text, clock['net'])
    for net in prepared['plan'].get('covered_data_nets', []):
        require_clock_preserved(before_text, after_text, net)
    intervention['original_data_routes_preserved'] = prepared['plan'].get('covered_data_nets', [])
    intervention['clock_prepared_before_router_initialization'] = True
    intervention['original_clock_route_preserved'] = True
    intervention['added_diodes'] = 3
    intervention['clock_preparation'] = prepared['clock_receipt']
    intervention['diode_placements'].update(prepared['clock_receipt']['diode_placements'])

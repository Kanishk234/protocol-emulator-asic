"""Bounded three-diode/one-buffer diagnostic for the frozen C-selector source."""
import json
import math
import os
from pathlib import Path

from local_antenna_repair import snapshot
from checked_openroad_tcl import checked, placement_command


def canonical(name):
    return name.replace('\\[', '[').replace('\\]', ']')


def diode_seed(anchor, item, units, bound):
    offset = item.get('seed_offset_um', [0, 0])
    if len(offset) != 2 or any(type(v) not in (int, float) or not math.isfinite(v)
                              or abs(v) > bound for v in offset):
        raise ValueError('Invalid bounded diode seed offset')
    return tuple(value + round(delta * units) for value, delta in zip(anchor, offset))


def audit_snapshot(before, after, plan, units):
    sizing = plan['sizing']
    diodes = {item['name']: item for item in plan['diodes']}
    assert set(after) == set(before) | set(diodes), 'Unexpected cell inventory'
    movable = {item['instance']: item for item in sizing}
    distance = plan['maximum_displacement_um'] * units
    for name, original in before.items():
        current = after[name]
        assert current['pins'] == original['pins'], 'Original connection changed: ' + name
        if name not in movable:
            assert current == original, 'Unrelated cell changed: ' + name
        else:
            assert original['master'] == movable[name]['original_master']
            assert current['master'] == movable[name]['candidate_master']
            assert current['status'] == original['status']
            assert all(abs(a-b) <= distance for a, b in zip(current['location'], original['location'])), 'Buffer moved too far'
    for name, diode in diodes.items():
        current = after[name]
        assert current['master'] == 'sg13cmos5l_antennanp'
        assert canonical(current['pins']['A']) == diode['net'], 'Wrong diode net'
        anchor = before[diode['anchor']]['location']
        assert all(abs(a-b) <= distance for a, b in zip(current['location'], anchor)), 'Diode moved too far'
        if 'required_displacement_y_um' in diode:
            low, high = diode['required_displacement_y_um']
            dy = (current['location'][1] - anchor[1]) / units
            assert low <= dy <= high, 'Clock diode left reviewed corridor'


def apply(design, router, database):
    import odb
    plan = json.loads(Path('spikes/phase2_stock_flow/c_select_local_repair_plan.json').read_text())
    manifest = json.loads(Path(os.environ['SOURCE_MANIFEST']).read_text())
    assert manifest['run']['id'] == plan['source_run'], 'Repair plan belongs to another source'
    block = database.getChip().getBlock()
    units = block.getDbUnitsPerMicron()
    before = snapshot(block)
    seeds = {}
    allowed = {item['instance'] for item in plan['sizing']}
    diode_master = database.findMaster('sg13cmos5l_antennanp')
    assert diode_master is not None
    for item in plan['sizing']:
        assert before[item['instance']]['master'] == item['original_master']
        assert database.findMaster(item['candidate_master']) is not None
    for item in plan['diodes']:
        assert item['name'] not in before
        anchor = block.findInst(item['anchor'])
        assert anchor is not None and anchor.getMaster().getName() == item['anchor_master']
        term = anchor.findITerm(item['pin'])
        assert term is not None and term.getNet() is not None
        assert canonical(term.getNet().getName()) == item['net']
        seeds[item['name']] = diode_seed(anchor.getLocation(), item, units,
                                         plan['maximum_displacement_um'])
    locked = []
    try:
        for inst in block.getInsts():
            if inst.getName() not in allowed and str(inst.getPlacementStatus()) in ('PLACED', 'FIRM'):
                locked.append((inst, inst.getPlacementStatus()))
                inst.setPlacementStatus('LOCKED')
        for item in plan['sizing']:
            inst = block.findInst(item['instance'])
            assert inst.swapMaster(database.findMaster(item['candidate_master']))
        for item in plan['diodes']:
            anchor = block.findInst(item['anchor'])
            net = anchor.findITerm(item['pin']).getNet()
            diode = odb.dbInst.create(block, diode_master, item['name'])
            diode.setOrient(anchor.getOrient())
            diode.setLocation(*seeds[item['name']])
            diode.setPlacementStatus('PLACED')
            diode.findITerm('A').connect(net)
            router.addDirtyNet(net)
        distance = plan['maximum_displacement_um']
        checked(design, placement_command(distance))
        checked(design, 'check_placement -verbose')
        for name in allowed:
            for term in block.findInst(name).getITerms():
                net = term.getNet()
                if net and str(net.getSigType()) not in ('POWER', 'GROUND'):
                    router.addDirtyNet(net)
    finally:
        for inst, status in locked:
            inst.setPlacementStatus(status)
    audit_snapshot(before, snapshot(block), plan, units)
    return dict(_before=before, _plan=plan, _units=units,
                allowed=plan['allowed_signal_nets_to_reroute'],
                added_diodes=len(plan['diodes']), diagnostic_only=True,
                placement_checked=True,
                clock_net_changed=True, clock_timing_must_be_remeasured=True)


def verify_after_router(database, intervention):
    before = intervention.pop('_before')
    plan = intervention.pop('_plan')
    units = intervention.pop('_units')
    after = snapshot(database.getChip().getBlock())
    audit_snapshot(before, after, plan, units)
    intervention['diode_placements'] = {
        item['name']: dict(location_dbu=after[item['name']]['location'],
                           orientation=after[item['name']]['orientation'],
                           anchor=item['anchor'], displacement_um=[
                               (a-b)/units for a,b in zip(after[item['name']]['location'],
                                                         before[item['anchor']]['location'])])
        for item in plan['diodes']}
    intervention['post_router_placement_and_connections_verified'] = True

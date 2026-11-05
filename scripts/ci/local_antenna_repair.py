"""Bounded diagnostic edits; called only inside an initialized incremental router."""
import json
from pathlib import Path


def snapshot(block):
    return {i.getName(): dict(master=i.getMaster().getName(), location=tuple(i.getLocation()),
                             orientation=str(i.getOrient()), status=str(i.getPlacementStatus()),
                             pins={t.getMTerm().getName(): t.getNet().getName() if t.getNet() else None
                                   for t in i.getITerms()}) for i in block.getInsts()}


def apply(design, router, database):
    import odb
    block = database.getChip().getBlock()
    before = snapshot(block)
    policy = json.loads(Path('spikes/phase2_stock_flow/targeted_locality_plan.json').read_text())
    sizes = json.loads(Path('spikes/phase2_stock_flow/antenna_targeted_sizing_feasibility.json').read_text())['cases']
    allowed = set(policy['movable_original_instances'])
    assert allowed <= set(before)
    for item in sizes:
        assert before[item['instance']]['master'] == item['original_master']
        assert database.findMaster(item['candidate_master']) is not None
    target = block.findInst('hold7969').findITerm('A').getNet()
    assert target.getName() == '_10511_'
    master = database.findMaster('sg13cmos5l_antennanp')
    assert master is not None and block.findInst('tripwire_local_diode') is None
    locked = []
    try:
        for inst in block.getInsts():
            if inst.getName() not in allowed and str(inst.getPlacementStatus()) in ('PLACED', 'FIRM'):
                locked.append((inst, inst.getPlacementStatus()))
                inst.setPlacementStatus('LOCKED')
        for item in sizes:
            inst = block.findInst(item['instance'])
            assert inst.swapMaster(database.findMaster(item['candidate_master']))
        diode = odb.dbInst.create(block, master, 'tripwire_local_diode')
        anchor = block.findInst('hold7969')
        diode.setOrient(anchor.getOrient())
        diode.setLocation(*anchor.getLocation())
        diode.setPlacementStatus('PLACED')
        diode.findITerm('A').connect(target)
        router.addDirtyNet(target)
        design.evalTclString('detailed_placement')
        design.evalTclString('check_placement -verbose')
        for name in allowed:
            for term in block.findInst(name).getITerms():
                net = term.getNet()
                if net and str(net.getSigType()) not in ('POWER', 'GROUND'):
                    router.addDirtyNet(net)
    finally:
        for inst, status in locked:
            inst.setPlacementStatus(status)
    after = snapshot(block)
    replacements = {i['instance']: i['candidate_master'] for i in sizes}
    audit_snapshot(before, after, allowed, replacements)
    return dict(_before=before, _allowed_instances=allowed, _replacements=replacements,
                allowed=policy['allowed_signal_nets_to_reroute'],
                changed_original_placements=[n for n in before if before[n]['location'] != after[n]['location'] or before[n]['orientation'] != after[n]['orientation']],
                original_connections_preserved=True, added_diodes=1, diagnostic_only=True)


def audit_snapshot(before, after, allowed, replacements):
    assert set(after) == set(before) | {'tripwire_local_diode'}, 'Unexpected cell inventory'
    for name, original in before.items():
        current = after[name]
        assert current['pins'] == original['pins'], 'Original pin connection changed: ' + name
        assert current['master'] == replacements.get(name, original['master'])
        if name not in allowed:
            assert current == original, 'Unrelated placement/status changed: ' + name


def verify_after_router(database, intervention):
    before = intervention.pop('_before')
    allowed = intervention.pop('_allowed_instances')
    replacements = intervention.pop('_replacements')
    after = snapshot(database.getChip().getBlock())
    audit_snapshot(before, after, allowed, replacements)
    assert after['tripwire_local_diode']['master'] == 'sg13cmos5l_antennanp'
    assert after['tripwire_local_diode']['pins']['A'] == '_10511_'
    intervention['post_router_placement_and_connections_verified'] = True

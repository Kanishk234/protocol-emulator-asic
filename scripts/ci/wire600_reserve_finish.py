"""Extend the exact wire600 identity plan with six measured reserve repairs."""
import copy
import hashlib
import json
from pathlib import Path
import re

from combined_physical_plan import connections
from electrical_repair_plan import validate_change as audit_buffers
from event_nor2_screen import logical_cells
from incremental_repair_audit import placements
from wire600_selective_plan import (BINDING, nearest_row, partition, plan as base_plan,
                                    power_anchor, source_rows)
from wire600_selective_screen import main as screen

REVIEW = json.loads((Path(__file__).parent/'fixtures/wire600_selective/reserve_finish.json').read_text())


def _build(root, macro_lef, review=REVIEW):
    proposal = copy.deepcopy(base_plan(root, macro_lef))
    layout = (Path(root)/BINDING['files']['def']['path']).read_text()
    nets, _ = connections(layout, True)
    loc = placements(layout)
    rows = source_rows(layout)
    # Preserve frozen fixture order so an appended repair retains all existing
    # buffer identities and adds only the final new group.
    for net, expected in review['extra_sources'].items():
        if sorted(map(list, nets[net])) != expected['terms']:
            raise ValueError('Residual source connectivity changed')
        driver, groups = partition(nets[net], loc)
        if list(driver) != expected['driver']:
            raise ValueError('Residual source driver changed')
        for sinks in groups:
            name = f'tripwire_wire600_{len(proposal["groups"])}'
            proposal['groups'].append(dict(buffer=name, net=name+'_net', source_net=net,
                rail_source=power_anchor(nets[net], loc, driver), master='sg13cmos5l_buf_4',
                sinks=sinks, location=nearest_row(rows, loc[driver[0]][1:3]), reasons=list(expected.get('reasons', ['slew']))))
        proposal['source_targets'][net] = list(expected.get('reasons', ['slew']))
    proposal['resizes'] = copy.deepcopy(review['resizes'])
    moved = {tuple(p) for g in proposal['groups'] for p in g['sinks']}
    for resize in proposal['resizes']:
        if loc[resize['instance']][0] != resize['old_master']:
            raise ValueError('Wrong resize source master')
        if any(n == resize['instance'] for n, p in moved):
            raise ValueError('Identity partition changes a resize input')
        outputs = [p for p in resize['pins'] if p in {'Q', 'X', 'Y'}]
        if len(outputs) != 1:
            raise ValueError('Resize must have one reviewed output')
        pin = outputs[0]
        proposal['source_targets'][resize['pins'][pin]] = ['capacitance' if pin == 'Q' else 'slew']
    proposal.update(buffers=len(proposal['groups']), target_count=len(proposal['source_targets']),
                    residual_evidence_run=review['evidence_run'])
    return proposal


def validate_proposal(proposal, review=REVIEW):
    if hashlib.sha256(json.dumps(proposal, sort_keys=True).encode()).hexdigest() != review['proposal_sha256']:
        raise ValueError('Unreviewed residual repair proposal')


def plan(root, macro_lef, review=REVIEW):
    result = _build(root, macro_lef, review)
    validate_proposal(result, review)
    return result


def target_call(layout, proposal, review=REVIEW):
    validate_proposal(proposal, review)
    if hashlib.sha256(layout.encode()).hexdigest() != BINDING['files']['def']['sha256']:
        raise ValueError('Wrong residual source DEF')
    nets, _ = connections(layout, True)
    loc = placements(layout)
    def word(value):
        if not re.fullmatch(r'[A-Za-z0-9_./\[\]-]+', value):
            raise ValueError('Unsafe residual Tcl identity')
        return '{'+value+'}'
    lines = []
    # First preserve the complete original identity partitions. Size afterwards
    # so their original-master preflights still inspect the untouched masters.
    for net in dict.fromkeys(g['source_net'] for g in proposal['groups']):
        groups = [g for g in proposal['groups'] if g['source_net'] == net]
        terms = nets[net]
        expected = '{'+word(net)+' {'+' '.join(word(n+'/'+p) for n, p in terms)+'} {'
        expected += ' '.join('{'+word(n)+' '+word(loc[n][0])+'}' for n in sorted({n for n, p in terms}))+'}}'
        serialized = []
        for g in groups:
            values = ' '.join(word(g[k]) for k in ('buffer', 'net', 'source_net', 'rail_source'))
            sinks = ' '.join('{'+word(n)+' '+word(p)+'}' for n, p in g['sinks'])
            serialized.append('{'+values+' {'+' '.join(map(str, g['location']))+'} {'+sinks+'}}')
        lines.append('tripwire_electrical_repair {sg13cmos5l_buf_4} {'+expected+'} {'+' '.join(serialized)+'}')
    targets = []
    for r in proposal['resizes']:
        pins = ' '.join(word(p)+' '+word(n) for p, n in sorted(r['pins'].items()))
        targets.append('{'+word(r['instance'])+' '+word(r['old_master'])+' '+word(r['new_master'])+' {'+pins+'}}')
    # The hook freezes existing placement before edits. Only these two wider
    # cells may move during legalization; all original statuses are restored.
    for r in proposal['resizes']:
        lines.append('[tripwire_electrical_find_inst [ord::get_db_block] '+word(r['instance'])+'] setPlacementStatus PLACED')
    lines.append('tripwire_size_electrical {'+' '.join(targets)+'}')
    return '\n'.join(lines)+'\n'


def resized_reference(before, proposal, review=REVIEW):
    validate_proposal(proposal, review)
    old = logical_cells(before)
    result = before
    for r in proposal['resizes']:
        # Normalize escaped names only; retain every exact port connection.
        master, pins = old.get(r['instance'], (None, ()))
        if master != r['old_master'] or {p: n.strip().removeprefix('\\') for p, n in pins} != r['pins']:
            raise ValueError('Wrong residual resize connections')
        pattern = r'\b'+re.escape(r['old_master'])+r'(\s+)'+re.escape(r['instance'])+r'(?=\s*\()'
        result, count = re.subn(pattern, lambda m: r['new_master']+m[1]+r['instance'], result)
        if count != 1:
            raise ValueError('Ambiguous residual resize')
    return result


def validate_change(before, after, proposal, review=REVIEW):
    return audit_buffers(resized_reference(before, proposal, review), after, {'groups': proposal['groups']})


def main():
    screen(plan_builder=plan, target_emitter=target_call, connectivity_audit=validate_change,
           output=Path('runs/wire600-reserve-finish-screen'))


if __name__ == '__main__':
    main()

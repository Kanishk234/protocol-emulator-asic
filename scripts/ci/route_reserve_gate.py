"""Internal fanout reserve on reviewed repair families; signoff limits stay fixed."""
import json
from pathlib import Path
from combined_physical_plan import connections


def measure(layout, proposal):
    nets, _ = connections(layout, True)
    selected = {g['source_net'] for g in proposal['groups']} | {g['net'] for g in proposal['groups']}
    if not selected:
        raise ValueError('Missing repaired net families')
    loads = {}
    for name in sorted(selected):
        terms = nets[name]
        if len([p for p in terms if p[1] in ('X', 'Y', 'Q')]) != 1:
            raise ValueError('Reserve net has no unique standard-cell driver')
        loads[name] = len(terms)-1
    return dict(internal_maximum_loads=6, loads=loads,
                fanout_reserve_pass=all(n <= 6 for n in loads.values()))


def enforce(root):
    root = Path(root)
    states = list((root/'grt').glob('*-openroad-globalrouting/state_out.json'))
    if len(states) != 1:
        raise ValueError('Missing unique fresh GRT state')
    state = json.loads(states[0].read_text())
    result = measure(Path(state['def']).read_text(), json.loads((root/'proposal.json').read_text()))
    path = root/'gates.json'
    receipt = json.loads(path.read_text())
    receipt.update(result)
    receipt['qualified'] = receipt['qualified'] and result['fanout_reserve_pass']
    path.write_text(json.dumps(receipt, indent=2)+'\n')
    if not result['fanout_reserve_pass']:
        raise ValueError('Internal repaired-family fanout reserve fails; no DRT')

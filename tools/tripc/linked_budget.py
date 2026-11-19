"""Conditional digital budget for an open-drain, linked low-bit response.

Pipeline constants come from ARCHITECTURE P1/P2/P6 and F1. Timing profiles are
declared environment inputs, not permission to change physical/signoff gates.
Entry, stream-selection and queue premises must hold; this is not their proof.
"""
from collections.abc import Mapping

import tripwire_spec as S

from .reaction import _fields
from .response import compiled_image_hash


RX_PUBLISH = 3  # two input synchronizer stages plus RX producer visibility
TX_ACCEPT = 1  # free linked TX accepts a visible producer token
EDGE_TO_DRIVE = 3  # external B edge to linked pad-register update (P6)
OBSERVATION_RESERVE = 1
ASSUMPTIONS = [
    'The final RX sampling edge completes the held token, with a free RX producer and no event collision.',
    'Every entry and no-arrival premise of the single-token lane query holds.',
    'The linked transmitter is initially idle, logically enabled, and selected; selection stays active through the following sample phase.',
    'No configuration/owner/host writes occur, and the checked DATA-only stream remains in effect.',
    'Declared edge gaps and setup requirements apply in clocks at the actual operating clock.',
    'This is a sampled digital timing contract, not pad/metastability/analog characterization.',
]


def _validate(contract):
    if not isinstance(contract, Mapping) or set(contract) != {'unit', 'profiles'}:
        raise ValueError('Linked budget requires only unit and profiles')
    if not isinstance(contract['unit'], str):
        raise ValueError('Linked budget unit must be a pin-unit name')
    profiles = contract['profiles']
    if not isinstance(profiles, Mapping) or not profiles:
        raise ValueError('Linked budget profiles must be nonempty')
    keys = {'response_edge_min', 'sample_edge_min', 'required_setup'}
    for name, profile in profiles.items():
        if not isinstance(name, str) or not name or not name.replace('_', '').isalnum():
            raise ValueError('Invalid linked profile name')
        if not isinstance(profile, Mapping) or set(profile) != keys:
            raise ValueError('Linked profile needs response_edge_min, sample_edge_min and required_setup')
        if any(type(v) is not int or not 1 <= v <= 65535 for v in profile.values()):
            raise ValueError('Linked profile values must be positive clock counts up to 65535')


def compose_linked_response(image, response, contract):
    _validate(contract)
    result = {'status': 'unsupported', 'assumptions': ASSUMPTIONS.copy(),
              'pipeline_clocks': {'rx_publish': RX_PUBLISH, 'tx_accept': TX_ACCEPT,
                                  'edge_to_drive': EDGE_TO_DRIVE,
                                  'observation_reserve': OBSERVATION_RESERVE},
              'entry_premises_proven': False, 'unconditional_pin_bound': False}

    def refuse(reason):
        return dict(result, reason=reason)

    if response['status'] != 'bounded':
        return refuse('The lane response query is not bounded')
    if response.get('compiled_image_sha256') != compiled_image_hash(image):
        return refuse('Lane response result does not match this compiled image')
    q = response['query']
    unit = contract['unit']
    cfg = image['pins'].get(unit)
    if cfg is None:
        return refuse('Unit is absent from the compiled image')
    if (cfg.get('rxmode') != 'linked_rx' or cfg.get('rx_edge', 'rise') != 'rise'
            or cfg.get('txmode') != 'shift' or cfg.get('tx_edge') != 'fall'
            or not cfg.get('tx_lentok', False) or cfg.get('tx_preload', False)
            or not cfg.get('od', False) or cfg.get('idle', 1) != 1
            or cfg.get('carrier', 0)):
        return refuse('Requires linked rise RX, non-preloaded fall TX, length tokens, idle-high open drain and no carrier')
    external = {p for group in ('ui', 'uio')
                for p in range(S.PAD_GROUPS[group][0], sum(S.PAD_GROUPS[group][:2]))}
    if cfg.get('pin_b') not in external:
        return refuse('The clock must be an attached external input with the P1 synchronizer contract')
    if [cfg.get('pin_a'), int(unit[1:])] not in image['own']:
        return refuse('The unit must own its response output pad')
    if q['input_tag'] != 'DATA' or q['response_tag'] != 'DATA' or q['response_data'] != 0:
        return refuse('This budget covers a single low DATA bit')
    for port, producer in [(f"{q['lane']}.{q['input_port']}", f'{unit}.rx'),
                            (f'{unit}.tx', f"{q['lane']}.{q['response_port']}")]:
        matches = [row for row in image['connect'] if row[0] == port]
        if (len(matches) != 1 or matches[0][1] != producer or matches[0][2] != 'blocking'
                or not matches[0][3] & (1 << S.TAGS['DATA'])):
            return refuse('Query ports must use the checked blocking RX/TX connections accepting DATA')
    target = S.DST[q['response_port']]
    for word in image['lanes'][q['lane']]['slots']:
        f = _fields(int(word, 16))
        if not f['V']:
            continue
        if f['OP'] == S.OPS['CALL']:
            return refuse('A CALL could introduce an unchecked routine output stream')
        if f['DST'] != target:
            continue
        if f['OP'] == S.OPS['MKCTL']:
            return refuse('The output stream can contain CTRL commands')
        if f['KT'] and f['ASRC'] in (S.ASRC['I0'], S.ASRC['I1']):
            if not (f['TE'] and f['TAG'] == S.TAGS['DATA']):
                return refuse('Kept output tags are not statically limited to DATA')
        elif f['OT'] != S.TAGS['DATA']:
            return refuse('The output stream is not DATA-only')
    arm = RX_PUBLISH + response['bound_clocks'] + TX_ACCEPT
    profiles = {}
    for name, p in contract['profiles'].items():
        ready_margin = p['response_edge_min'] - arm - OBSERVATION_RESERVE
        setup_bound = p['sample_edge_min'] - EDGE_TO_DRIVE - OBSERVATION_RESERVE
        profiles[name] = {**p, 'armed_by_clocks': arm,
                          'ready_margin_clocks': ready_margin,
                          'target_low_setup_bound_clocks': setup_bound,
                          'passes': ready_margin >= 0 and setup_bound >= p['required_setup']}
    return {**result, 'status': 'conditional_pass' if all(p['passes'] for p in profiles.values())
            else 'insufficient_budget', 'unit': unit, 'profiles': profiles}


def linked_budget_report(results):
    lines = ['## Conditional linked-edge budget', '',
             'Entry and queue premises are NOT proved by this composition. Numbers are sampled '
             'digital clocks, not WNS or characterized pad timing.', '',
             '| Query/profile | Armed by | Ready margin | Target-low setup bound | Required setup | Status |',
             '|---|---|---|---|---|---|']
    for name, response in results.items():
        budget = response['linked_budget']
        if budget['status'] == 'unsupported':
            lines.append(f"| {name} | — | — | — | — | unsupported: {budget['reason']} |")
        for profile, p in budget.get('profiles', {}).items():
            lines.append(f"| {name}/{profile} | {p['armed_by_clocks']} | {p['ready_margin_clocks']} | "
                         f"{p['target_low_setup_bound_clocks']} | {p['required_setup']} | "
                         f"{'conditional pass' if p['passes'] else 'insufficient'} |")
    lines += ['', 'Additional required premises:', ''] + [f'- {p}' for p in ASSUMPTIONS]
    return '\n'.join(lines) + '\n'

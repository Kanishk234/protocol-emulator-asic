"""Conditional single-token lane response checking from ISA §4.

Exhaustive over the query's listed input values and allowed initial flags.
Unknown register values propagate conservatively. This does not bound arrivals,
fabric service, routines, pin scheduling, or pin-to-pin latency.
"""
from collections.abc import Mapping
import hashlib
import json
import re

import tripwire_spec as S

from .reaction import WIDTHS, _fields, readiness


REQUIRED = {'lane', 'state', 'input_port', 'input_tag', 'input_values',
            'response_port', 'response_tag', 'response_data'}
OPTIONAL = {'flag_mask', 'flag_value', 'registers', 'max_clocks'}
ASSUMPTIONS = [
    'Clock 0 begins with the specified input token visible at an eligible EVAL.',
    'The lane runs every clock, with no routine, pending flag or EXEC action initially.',
    'The other input is empty; no new tokens or host writes arrive during the query.',
    'The held token disappears only if a selected action dequeues it.',
    'Both output producers are initially free; an earlier output or CALL is outside this contract.',
    'Constants are the compiled constants; only explicitly supplied register values are assumed.',
    'The endpoint is response-token visibility, not an input pin or output pin edge.',
]


def _integer(value, upper, label):
    if type(value) is not int or not 0 <= value < upper:
        raise ValueError(f'{label} must be an integer in [0, {upper})')
    return value


def _query(image, query):
    if not isinstance(query, Mapping) or not REQUIRED <= query.keys() or query.keys() - REQUIRED - OPTIONAL:
        raise ValueError('Response query has missing or unknown fields')
    q = dict(query)
    if not isinstance(q['lane'], str) or q['lane'] not in image['lanes']:
        raise ValueError('Unknown response-query lane')
    lane = image['lanes'][q['lane']]
    if isinstance(q['state'], str):
        if q['state'] not in lane['states']:
            raise ValueError('Unknown response-query state')
        q['state'] = lane['states'][q['state']]
    _integer(q['state'], 16, 'state')
    if q['input_port'] not in ('I0', 'I1') or q['response_port'] not in ('O0', 'O1'):
        raise ValueError('Response query needs I0/I1 and O0/O1')
    for name in ('input_tag', 'response_tag'):
        if not isinstance(q[name], str) or q[name] not in S.TAGS:
            raise ValueError(f'Unknown {name}')
    if not isinstance(q['input_values'], list) or not q['input_values']:
        raise ValueError('input_values must be a nonempty explicit list')
    for value in q['input_values']:
        _integer(value, 1 << S.DATA_BITS, 'input value')
    if len(set(q['input_values'])) != len(q['input_values']):
        raise ValueError('Duplicate input values')
    if len(q['input_values']) > 8192:
        raise ValueError('Response queries support at most 8192 explicit input values')
    q['input_values'] = list(q['input_values'])
    _integer(q['response_data'], 1 << S.DATA_BITS, 'response data')
    q.setdefault('flag_mask', 0)
    q.setdefault('flag_value', 0)
    for name in ('flag_mask', 'flag_value'):
        _integer(q[name], 8, name)
    if q['flag_value'] & ~q['flag_mask']:
        raise ValueError('flag_value sets bits outside flag_mask')
    q.setdefault('registers', {})
    if not isinstance(q['registers'], Mapping) or set(q['registers']) - {'r0', 'r1', 'r2', 'r3'}:
        raise ValueError('registers must map r0..r3 to assumed values')
    for value in q['registers'].values():
        _integer(value, 1 << S.DATA_BITS, 'register value')
    q['registers'] = dict(q['registers'])
    q.setdefault('max_clocks', 64)
    _integer(q['max_clocks'], 4097, 'max_clocks')
    if not q['max_clocks']:
        raise ValueError('max_clocks must be positive')
    return q, lane


def _alu(f, a, b, regs, constants):
    """Known values from ISA §3; None denotes an unknown value, never zero."""
    op, imm = f['OP'], f['IMM']
    flag = None
    if op == S.OPS['MOVB']:
        data = b
    elif op in (S.OPS['MOV'], S.OPS['CMPM'], S.OPS['LTU'], S.OPS['PAR']):
        data = a
        if op == S.OPS['CMPM']:
            bank = constants if imm & 16 else regs
            mask, value = bank[imm & 3], bank[imm >> 2 & 3]
            flag = None if None in (a, mask, value) else int(a & mask == value)
        elif op == S.OPS['LTU']:
            flag = None if None in (a, b) else int(a < b)
        elif op == S.OPS['PAR']:
            flag = None if a is None else a.bit_count() & 1
    elif op == S.OPS['MKCTL']:
        data = None if a is None else (imm >> 4 << 12) | (a & 0xFFF)
    elif op == S.OPS['EXT']:
        data = None if a is None else (a >> (imm & 15)) & ((1 << ((imm >> 4) + 1)) - 1)
    elif op == S.OPS['SHOR']:
        other = regs[imm >> 4 & 3]
        data = None if None in (a, other) else (a << (imm & 15)) | other
    elif a is None or b is None:
        data = None
    elif op == S.OPS['ADD']:
        data = a + b
    elif op == S.OPS['SUB']:
        data = a - b
    elif op == S.OPS['AND']:
        data = a & b
    elif op == S.OPS['OR']:
        data = a | b
    elif op == S.OPS['XOR']:
        data = a ^ b
    elif op == S.OPS['SHL']:
        data = a << (b & 15)
    elif op == S.OPS['SHR']:
        data = a >> (b & 15)
    else:
        raise ValueError('Unsupported response operation')
    if data is not None:
        data &= (1 << S.DATA_BITS) - 1
    if op not in (S.OPS['CMPM'], S.OPS['LTU'], S.OPS['PAR']):
        flag = None if data is None else int(data == 0)
    return data, flag


def _case(lane, q, value, flags):
    words = [int(w, 16) for w in lane['slots']]
    fields = [_fields(w) for w in words]
    regs = [q['registers'].get(f'r{i}') for i in range(4)]
    state, pending, available, executing = q['state'], 0, True, None
    source = S.ASRC[q['input_port']]
    target = S.DST[q['response_port']]
    trace, visited = [], set()

    def finish(status, reason, **extra):
        return {'input': value, 'initial_flags': initial_flags, 'status': status,
                'reason': reason, 'trace': trace, **extra}

    initial_flags = flags
    for clock in range(q['max_clocks']):
        # EXEC and EVAL both read pre-edge state. EXEC result is committed only
        # after selection. A response committed at edge n is visible in n+1.
        write_reg = write_flag = None
        if executing is not None:
            index, held = executing
            f = fields[index]
            a = regs[f['ASRC']] if f['ASRC'] < 4 else held
            if f['ASRC'] == S.ASRC['zero']:
                a = 0
            # Global time is deliberately unknown; a clock-0 value is not assumed.
            if f['ASRC'] == S.ASRC['time']:
                a = None
            b = (regs[f['IMM'] & 3] if f['BSEL'] == S.BSEL['reg'] else
                 lane['k'][f['IMM'] & 3] if f['BSEL'] == S.BSEL['k'] else f['IMM'])
            data, flag = _alu(f, a, b, regs, lane['k'])
            if f['DST'] == target:
                if data is None:
                    return finish('unknown', 'Response depends on an unknown register or time')
                tag = (S.TAGS['CTRL'] if f['OP'] == S.OPS['MKCTL'] else
                       S.TAGS[q['input_tag']] if f['KT'] and f['ASRC'] == source else f['OT'])
                ok = data == q['response_data'] and tag == S.TAGS[q['response_tag']]
                return finish('bounded' if ok else 'counterexample',
                              'Expected response visible' if ok else 'Wrong response token',
                              response_clocks=clock + 1, response_tag=tag, response_data=data)
            if f['DST'] < 4:
                write_reg = f['DST'], data
            if f['DFE'] and f['DF'] < 3:
                if flag is None:
                    return finish('unknown', 'Flag result depends on an unknown register or time')
                write_flag = f['DF'], flag

        snapshot = (state, flags, pending, tuple(regs), available, executing)
        if snapshot in visited:
            return finish('unknown', 'Repeated abstract state before response')
        visited.add(snapshot)
        values = {'state': state, 'flags': flags, 'pending': pending,
                  'i0_avail': int(available and source == S.ASRC['I0']),
                  'i1_avail': int(available and source == S.ASRC['I1']),
                  'i0_tag': S.TAGS[q['input_tag']], 'i1_tag': S.TAGS[q['input_tag']],
                  'i0_data': value, 'i1_data': value, 'o0_free': 1, 'o1_free': 1}
        context = {name: ((1 << WIDTHS[name]) - 1, val) for name, val in values.items()}
        pick = next((i for i, word in enumerate(words) if readiness(word, context) is not None), None)
        trace.append({'clock': clock, 'state': state, 'flags': flags,
                      'pending': pending, 'slot': pick})
        if pick is not None:
            f = fields[pick]
            if f['OP'] == S.OPS['CALL']:
                return finish('unknown', 'CALL requires a routine/SRAM progress contract')
            if f['DST'] in (S.DST['O0'], S.DST['O1']) and f['DST'] != target:
                return finish('unknown', 'Earlier output requires a consumer-progress contract')
        elif executing is None:
            return finish('counterexample', 'No ready action or future arrival under this contract')

        if write_reg is not None:
            regs[write_reg[0]] = write_reg[1]
        if write_flag is not None:
            bit, flag = write_flag
            flags = (flags & ~(1 << bit)) | (flag << bit)
            pending &= ~(1 << bit)
        executing = None
        if pick is not None:
            f = fields[pick]
            executing = pick, value if f['ASRC'] == source else None
            if f['NSE']:
                state = f['NS']
            if f['DQ'] and f['ASRC'] == source:
                available = False
            if f['DFE'] and f['DF'] < 3:
                pending |= 1 << f['DF']  # EVAL set wins over an EXEC clear.
    return finish('unknown', 'Clock horizon reached before response')


def analyze_response(image, query):
    """Check a closed, single-token lane contract; never a pin timing certificate."""
    q, lane = _query(image, query)
    cases = [_case(lane, q, value, flags) for value in q['input_values']
             for flags in range(8) if flags & q['flag_mask'] == q['flag_value']]
    status = ('counterexample' if any(c['status'] == 'counterexample' for c in cases) else
              'unknown' if any(c['status'] == 'unknown' for c in cases) else 'bounded')
    return {'status': status, 'bound_clocks': max(c['response_clocks'] for c in cases)
            if status == 'bounded' else None, 'query': q,
            'assumptions': ASSUMPTIONS.copy(), 'cases': cases,
            'pin_to_pin_bound': False, 'deadlock_certificate': False,
            'compiled_image_sha256': compiled_image_hash(image)}


def compiled_image_hash(image):
    return hashlib.sha256(json.dumps(image, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def analyze_queries(image, queries):
    if not isinstance(queries, Mapping) or not queries:
        raise ValueError('Response queries must be a nonempty named mapping')
    if any(not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+', name)
           for name in queries):
        raise ValueError('Query names must use letters, digits, underscores, dots or hyphens')
    return {name: analyze_response(image, query) for name, query in queries.items()}


def response_report(results):
    lines = ['## Conditional single-token response', '',
             'Clock bounds below start at a visible input head and end at response-token visibility. '
             'They are NOT pin-to-pin or whole-program guarantees.', '',
             '| Query | Status | Cases | Response visible within (clocks) |', '|---|---|---|---|']
    for name, result in results.items():
        bound = result['bound_clocks'] if result['status'] == 'bounded' else 'unknown'
        lines.append(f"| {name} | {result['status']} | {len(result['cases'])} | {bound} |")
    lines += ['', 'Query domains (all clocks are lane-local):', '']
    for name, result in results.items():
        q = result['query']
        values = sorted(q['input_values'])
        groups = []
        first = last = values[0]
        for value in values[1:] + [None]:
            if value is not None and value == last + 1:
                last = value
                continue
            groups.append(hex(first) if first == last else f'{hex(first)}..{hex(last)}')
            first = last = value
        lines.append(f"- {name}: {q['lane']} STATE={q['state']}; {q['input_port']} {q['input_tag']} "
                     f"values {', '.join(groups)}; FLAGS & {hex(q['flag_mask'])} = {hex(q['flag_value'])}; "
                     f"expect {q['response_port']} {q['response_tag']} {hex(q['response_data'])}; "
                     f"register assumptions {q['registers']}; horizon {q['max_clocks']} clocks.")
    lines += ['', 'Required environment contract:', ''] + [f'- {a}' for a in ASSUMPTIONS]
    lines += ['', 'Every listed input and every allowed initial flag combination is checked. '
              'Unspecified registers remain unknown. Full contracts and traces are available with '
              '--response-results; unknown or failed queries give a nonzero exit status.', '']
    return '\n'.join(lines)

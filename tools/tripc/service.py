"""Conditional SRAM service envelope for acyclic, non-output routines.

Decode the emitted words from the encoding specification. Do not infer timing
from names, source text, or the compiler's max_steps metadata. This supplies no
arrival bound and deliberately refuses loops, output waits and state writes.
"""
import tripwire_spec as S

from .response import compiled_image_hash


ASSUMPTIONS = [
    'CALL has just been selected on a running lane with an initially idle routine pipeline.',
    'The lane owns one SRAM slot in every four clocks; no host/configuration writes occur.',
    'No reflex action is selected until RET completes; the routine is not halted or stepped.',
    'Data writes do not alias the entry table or executed routine words; encoded instructions remain unchanged.',
    'This is a service envelope, not a proof of queue freedom, arrival spacing or protocol deadlines.',
]


def _field(word, bounds):
    hi, lo = bounds
    return word >> lo & ((1 << (hi - lo + 1)) - 1)


def routine_service(image, name, *, reflex_budget=0):
    if type(reflex_budget) is not int or not 0 <= reflex_budget <= 65535:
        raise ValueError('reflex_budget must be an integer in [0, 65535]')
    assumptions = ASSUMPTIONS.copy()
    if reflex_budget:
        assumptions[2] = (f'At most {reflex_budget} reflex actions are selected before RET completes; '
                          'the routine is not halted or stepped.')
    result = {'status': 'unsupported', 'bound_clocks': None,
              'compiled_image_sha256': compiled_image_hash(image),
              'assumptions': assumptions, 'arrival_invariants_proven': False}

    def refuse(reason):
        return dict(result, reason=reason)

    info = image['routines'].get(name)
    if info is None:
        return refuse('Unknown routine')
    index, count = info['index'], info['words']
    sram = image['sram']
    if (type(index) is not int or not 0 <= index < 32 or index >= len(sram)
            or type(count) is not int or count < 1):
        return refuse('Invalid routine entry metadata')
    start = sram[index]
    if type(start) is not int or start < 32 or start + count > len(sram):
        return refuse('Routine words are outside the image')
    loads = stores = 0
    for n, word in enumerate(sram[start:start + count]):
        if type(word) is not int or not 0 <= word < (1 << S.ROUTINE_BITS):
            return refuse('Invalid encoded routine word')
        if not word >> (S.ROUTINE_BITS - 1):
            kind, fields = 'ALU', S.ROUTINE_ALU_FIELDS
            if _field(word, fields['op']) == S.OPS['CALL']:
                return refuse('Routine ALU CALL is unsupported')
        else:
            sub = _field(word, S.ROUTINE_CTRL_SUB)
            kind, fields = next((k, f) for k, (v, f) in S.ROUTINE_CTRL.items() if v == sub)
        if kind in ('DJNZ', 'OUT'):
            return refuse('Loops and output waits need a separate progress contract')
        if kind == 'BR':
            hi, lo = fields['off']
            offset = _field(word, (hi, lo))
            sign = 1 << (hi - lo)
            if offset & sign:
                offset -= sign << 1
            target = n + 1 + offset
            if not n < target < count:
                return refuse('Branch must target a later word inside the routine')
        if kind == 'SYS':
            if _field(word, fields['fn']) != S.SYS['RET'] or n != count - 1:
                return refuse('Requires exactly one terminal RET and no other SYS operation')
        elif n == count - 1:
            return refuse('Routine has no terminal RET')
        loads += kind == 'LD'
        stores += kind == 'ST'
    # A forward branch can only skip words, so charging every word and data
    # access in the routine bounds both paths.
    # Entry-table read, every instruction fetch, and each data read/write need
    # separate rotation slots (R1-R3). Without reflex interference, fetch ->
    # EVAL -> EXEC fits before the next slot. LD writeback also fits before it.
    # Charge a full four clocks per access, then three for terminal RET
    # delivery, including the observation after its EXEC edge. Starting on
    # the lane's rotation phase misses that edge's still-unrequested entry read.
    accesses = 1 + count + loads + stores
    # One reflex can delay a ready routine issue and thereby miss one owned
    # rotation. Charge one full rotation per selected action. The budget is
    # an explicit premise, not inferred from the number of incoming tokens.
    return {**result, 'status': 'conditional_bound',
            'bound_clocks': 4 * accesses + 3 + 4 * reflex_budget,
            'reflex_budget': reflex_budget, 'reflex_budget_proven': False,
            'instruction_fetches': count, 'data_reads': loads, 'data_writes': stores,
            'entry_reads': 1, 'sram_accesses': accesses,
            'data_write_nonalias_proven': stores == 0}

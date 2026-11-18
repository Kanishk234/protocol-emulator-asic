"""Local EVAL selection analysis from encoded ISA readiness predicates.

This is deliberately not an end-to-end reaction/deadlock proof. Predicate
overlap includes states that might be unreachable in the complete program.
Availability/free-output constraints are assumptions at one eligible EVAL,
not promises that channels will eventually make progress.
"""
from collections.abc import Mapping

import tripwire_spec as S


WIDTHS = {'state': 4, 'flags': 4, 'pending': 3,
          'i0_avail': 1, 'i0_tag': 2, 'i0_data': 16,
          'i1_avail': 1, 'i1_tag': 2, 'i1_data': 16,
          'o0_free': 1, 'o1_free': 1}


def _fields(word):
    if not isinstance(word, int) or not 0 <= word < 1 << S.SLOT_BITS:
        raise ValueError('Slot word does not fit the generated encoding')
    return {name: word >> shift & ((1 << width) - 1)
            for name, (shift, width) in S.SLOT_FIELDS.items()}


def _merge(left, right):
    """Intersect conjunctions of masked equalities; None means contradiction."""
    if left is None or right is None:
        return None
    out = dict(left)
    for name, (mask, value) in right.items():
        old_mask, old_value = out.get(name, (0, 0))
        if (old_value ^ value) & old_mask & mask:
            return None
        out[name] = old_mask | mask, old_value | value
    return out


def _context(context):
    if context is None:
        return {}
    if not isinstance(context, Mapping):
        raise ValueError('Context must map readiness variables to (mask, value)')
    result = {}
    for name, pair in context.items():
        if name not in WIDTHS or not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise ValueError(f'Invalid readiness context: {name}')
        mask, value = pair
        if (not isinstance(mask, int) or not isinstance(value, int)
                or not 0 <= mask < 1 << WIDTHS[name]
                or not 0 <= value < 1 << WIDTHS[name] or value & ~mask):
            raise ValueError(f'Invalid masked equality for {name}')
        result[name] = mask, value
    return result


def readiness(word, context=None):
    """Return a masked-equality conjunction for ISA §4.2, or None if impossible.

    Contexts constrain one EVAL snapshot. For example {'i0_tag': (3, DATA)}
    excludes an EVENT head; it does not prove that future EVENT arrivals stop.
    """
    f = _fields(word)
    cube = _context(context)
    if not f['V']:
        return None
    if f['SE']:
        cube = _merge(cube, {'state': (15, f['SV'])})
    cube = _merge(cube, {'flags': (f['FM'], f['FV'] & f['FM']),
                         'pending': (f['FM'] & 7, 0)})
    if f['ASRC'] in (S.ASRC['I0'], S.ASRC['I1']):
        port = f['ASRC'] - S.ASRC['I0']
        cube = _merge(cube, {f'i{port}_avail': (1, 1)})
        if f['TE']:
            cube = _merge(cube, {f'i{port}_tag': (3, f['TAG'])})
        if f['HE']:
            bit = 0 if f['HS'] else 15
            cube = _merge(cube, {f'i{port}_data': (1 << bit, f['HV'] << bit)})
    # CALL's implicit !RB check applies even without an explicit flag test.
    # Its encoded DST is ignored (ISA L10), including output-free checking.
    if f['OP'] == S.OPS['CALL']:
        cube = _merge(cube, {'flags': (8, 0)})
    elif f['DST'] in (S.DST['O0'], S.DST['O1']):
        cube = _merge(cube, {f"o{f['DST'] - S.DST['O0']}_free": (1, 1)})
    return cube


def overlap_witness(first, second, context=None):
    """A concrete co-ready snapshot, or None when the predicates are disjoint."""
    merged = _merge(readiness(first, context), readiness(second, context))
    if merged is None:
        return None
    return {name: merged.get(name, (0, 0))[1] for name in WIDTHS}


def analyze_lane(words, context=None):
    """Analyze each valid urgent slot in both ISA §4.3 scheduler modes.

    A zero count of possible earlier competitors proves selection *if ready*
    at that eligible EVAL. It does not establish readiness, channel progress,
    time to the next EVAL, register stability, or a pin-to-pin clock bound.
    """
    _context(context)  # Validate even for an empty lane.
    fields = [_fields(w) for w in words]
    results = []
    for index, (word, f) in enumerate(zip(words, fields)):
        if not f['V'] or not f['U']:
            continue
        possible = readiness(word, context) is not None
        before = [j for j in range(index)
                  if overlap_witness(words[j], word, context) is not None]
        urgent_before = [j for j in before if fields[j]['U']]
        results.append({'slot': index, 'predicate_possible': possible,
                        'competitors_no_routine': before,
                        'competitors_with_issuable_routine': urgent_before,
                        'selected_if_ready': possible and not before,
                        'selected_if_ready_with_issuable_routine': possible and not urgent_before})
    return results

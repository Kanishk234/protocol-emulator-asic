"""Conservative topology diagnostics for the compiler's channel report."""
import tripwire_spec as spec

from .reaction import readiness


def _field(word, name):
    shift, width = spec.SLOT_FIELDS[name]
    return (word >> shift) & ((1 << width) - 1)


def blocking_components(connections):
    """Return cyclic components in the actor graph of final blocking bindings."""
    final = {port: (producer, mode) for port, producer, mode, _ in connections}
    edges = {}
    for port, (producer, mode) in final.items():
        if mode == 'blocking':
            source, target = producer.split('.')[0], port.split('.')[0]
            edges.setdefault(source, set()).add(target)

    def reachable(start):
        seen = set()
        todo = list(edges.get(start, ()))
        while todo:
            node = todo.pop()
            if node not in seen:
                seen.add(node)
                todo.extend(edges.get(node, ()))
        return seen

    reach = {source: reachable(source) for source in edges}
    return sorted({
        tuple(sorted(peer for peer in downstream if source in reach.get(peer, ())))
        for source, downstream in reach.items() if source in downstream
    })


def forwarding_ports(words):
    """Return the input/output indices of a single unconditional forwarding slot."""
    slots = [int(word, 16) for word in words]
    slots = [word for word in slots if _field(word, 'V')]
    if len(slots) != 1:
        return None
    word = slots[0]
    if (
        _field(word, 'ASRC') in (spec.ASRC['I0'], spec.ASRC['I1'])
        and _field(word, 'DST') in (spec.DST['O0'], spec.DST['O1'])
        and _field(word, 'DQ')
        and _field(word, 'OP') != spec.OPS['CALL']
        and not any(_field(word, name) for name in ('SE', 'FM', 'TE', 'HE', 'NSE', 'DFE'))
    ):
        return _field(word, 'ASRC') - spec.ASRC['I0'], _field(word, 'DST') - spec.DST['O0']
    return None


def closed_forwarding_cycles(image, cycles):
    """Find unconditional forwarding groups whose inputs use the whole internal ring."""
    ports = {lane: forwarding_ports(data['slots']) for lane, data in image['lanes'].items()}
    bindings = {port: (producer, mode, accept) for port, producer, mode, accept in image['connect']}
    for group in cycles:
        if any(ports.get(lane) is None for lane in group):
            continue
        outputs = {f'{lane}.O{ports[lane][1]}' for lane in group}
        internal = {(output, 'blocking', 0xf) for output in outputs}
        incoming = {bindings.get(f'{lane}.I{ports[lane][0]}') for lane in group}
        if incoming == internal:
            yield group


def _lane_output_tags(producer, lanes):
    """Bound tags for reflex-only producers, treating other sources as unknown."""
    lane, _, output = producer.partition('.')
    if lane not in lanes or output not in ('O0', 'O1'):
        return 0xf
    words = [int(word, 16) for word in lanes[lane]['slots']]
    mask = 0
    for word in words:
        if not _field(word, 'V'):
            continue
        if _field(word, 'OP') == spec.OPS['CALL']:
            return 0xf
        if _field(word, 'DST') != spec.DST[output]:
            continue
        if _field(word, 'OP') == spec.OPS['MKCTL']:
            mask |= 1 << spec.TAGS['CTRL']
        elif _field(word, 'KT') and _field(word, 'ASRC') in (spec.ASRC['I0'], spec.ASRC['I1']):
            if not _field(word, 'TE'):
                return 0xf
            mask |= 1 << _field(word, 'TAG')
        else:
            mask |= 1 << _field(word, 'OT')
    return mask


def _states_from_reset(words, context=None):
    """Overapproximate reachable STATE with fixed slots and no host writes."""
    if any(_field(word, 'OP') == spec.OPS['CALL'] for word in words):
        return set(range(16))
    states = {0}
    transitions = [word for word in words if _field(word, 'NSE')
                   and readiness(word, context) is not None]
    while True:
        targets = {_field(word, 'NS') for word in transitions
                   if not _field(word, 'SE') or _field(word, 'SV') in states}
        if targets <= states:
            return states
        states.update(targets)


def undrainable_tags(image):
    """Find admitted lane input tags with no possible dequeue in the loaded slots."""
    bindings = {port: (producer, mode, accept) for port, producer, mode, accept in image['connect']}
    for lane, data in sorted(image['lanes'].items()):
        words = [int(word, 16) for word in data['slots']]
        words = [word for word in words if _field(word, 'V')]
        states = _states_from_reset(words)
        for index in range(2):
            port = f'{lane}.I{index}'
            if port not in bindings or bindings[port][1] != 'blocking':
                continue
            producer, _, accept = bindings[port]
            possible = accept & _lane_output_tags(producer, image['lanes'])
            dequeuers = [word for word in words if _field(word, 'DQ')
                         and _field(word, 'ASRC') == spec.ASRC[f'I{index}']]
            for name, tag in spec.TAGS.items():
                if not possible & (1 << tag):
                    continue
                context = {f'i{index}_tag': (3, tag)}
                matching = [word for word in dequeuers if readiness(word, context) is not None]
                if not matching:
                    yield port, name, False
                elif all(_field(word, 'SE') and _field(word, 'SV') not in states
                         for word in matching):
                    yield port, name, 'reset'
                else:
                    # Only condition on a held tag from reset state. In a nonzero
                    # arrival state the earlier transitions may already have fired.
                    held_states = _states_from_reset(words, context)
                    if all(_field(word, 'SE') and _field(word, 'SV') not in held_states
                           for word in matching):
                        yield port, name, 'held'


def report_channel_graph(image):
    """Report structural risks without declaring queue progress or a rate bound."""
    cycles = blocking_components(image['connect'])
    stages = [lane for lane, data in sorted(image['lanes'].items())
              if forwarding_ports(data['slots']) is None]
    lines = [
        '## Channel graph', '',
        'Topology diagnostics only. Queue progress and overrun depend on token arrivals, '
        'consumer service and executing code. This analysis provides no deadlock or rate certificate.',
    ]
    if cycles:
        lines += [f'- Potential blocking feedback among {", ".join(group)}.' for group in cycles]
    else:
        lines.append('- No blocking feedback found in the configured actor graph.')
    if stages:
        lines.append('- Service is unclassified for lanes with conditional, multiple or '
                     f'non-forwarding slots: {", ".join(stages)}.')
    for port, tag, unreachable in undrainable_tags(image):
        if unreachable == 'held':
            lines.append(f'- {port} can hold an accepted {tag} token indefinitely if it arrives '
                         'in reset STATE. With fixed slots and bindings and no host STATE writes, the held tag '
                         'rules out the transitions needed to enable its dequeue.')
        else:
            reason = ('All matching dequeue slots require a STATE unreachable from reset '
                      'with fixed slots and no host STATE writes.' if unreachable else
                      'No compiled slot can dequeue it with the loaded configuration.')
            lines.append(f'- {port} blocks its producer if it receives an accepted {tag} token. {reason}')
    for group in closed_forwarding_cycles(image, cycles):
        group_names = ', '.join(group)
        lines.append(f'- No forwarding can start from empty channels in {group_names} '
                     'under the compiled slot and binding configuration.')
        lines.append(f'- A fully occupied forwarding ring in {group_names} cannot advance '
                     'while every internal blocking receiver is waiting on its full output. '
                     'This check does not establish whether the full state is reachable.')
    return lines

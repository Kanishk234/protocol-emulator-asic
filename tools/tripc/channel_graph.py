"""Conservative topology diagnostics for the compiler's channel report."""
import tripwire_spec as spec


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
    def field(word, name):
        shift, width = spec.SLOT_FIELDS[name]
        return (word >> shift) & ((1 << width) - 1)

    slots = [int(word, 16) for word in words]
    slots = [word for word in slots if field(word, 'V')]
    if len(slots) != 1:
        return None
    word = slots[0]
    if (
        field(word, 'ASRC') in (spec.ASRC['I0'], spec.ASRC['I1'])
        and field(word, 'DST') in (spec.DST['O0'], spec.DST['O1'])
        and field(word, 'DQ')
        and field(word, 'OP') != spec.OPS['CALL']
        and not any(field(word, name) for name in ('SE', 'FM', 'TE', 'HE', 'NSE', 'DFE'))
    ):
        return field(word, 'ASRC') - spec.ASRC['I0'], field(word, 'DST') - spec.DST['O0']
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
    for group in closed_forwarding_cycles(image, cycles):
        group_names = ', '.join(group)
        lines.append(f'- No forwarding can start from empty channels in {group_names} '
                     'under the compiled slot and binding configuration.')
        lines.append(f'- A fully occupied forwarding ring in {group_names} cannot advance '
                     'while every internal blocking receiver is waiting on its full output. '
                     'This check does not establish whether the full state is reachable.')
    return lines

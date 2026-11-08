"""Read-only saved-grid and target-net evidence; no repair or qualification."""
import hashlib
import json
from pathlib import Path
import re


def saved_overflow(grid, layers):
    xs, ys = list(grid.getGridX()), list(grid.getGridY())
    if len(xs) < 2 or len(ys) < 2:
        raise ValueError('Missing native routing grid')
    if any(b <= a for points in (xs, ys) for a, b in zip(points, points[1:])):
        raise ValueError('Invalid grid coordinates')
    rows = []
    for layer in layers:
        direction = str(layer.getDirection())
        if direction not in ('HORIZONTAL', 'VERTICAL'):
            raise ValueError('Unknown preferred routing direction')
        horizontal = direction == 'HORIZONTAL'
        for x in range(len(xs)):
            for y in range(len(ys)):
                cap, used = int(grid.getCapacity(layer, x, y)), int(grid.getUsage(layer, x, y))
                if cap < 0 or used < 0:
                    raise ValueError('Negative capacity or usage')
                if used <= cap:
                    continue
                if (horizontal and x + 1 == len(xs)) or (not horizontal and y + 1 == len(ys)):
                    raise ValueError('Overflow at terminal grid boundary')
                rows.append(dict(layer=layer.getName(), x_index=x, y_index=y,
                                 lower_gcell_origin_dbu=[xs[x], ys[y]],
                                 upper_gcell_origin_dbu=[xs[x + 1] if horizontal else xs[x],
                                                        ys[y] if horizontal else ys[y + 1]],
                                 capacity=cap, usage=used, overflow=used-cap))
    return rows


def find_net(block, name):
    escaped = name.replace('[', r'\[').replace(']', r'\]')
    matches = {}
    for spelling in sorted({name, escaped}):
        net = block.findNet(spelling)
        if net is not None:
            matches[net.getName()] = net
    if len(matches) != 1:
        raise ValueError('Missing or ambiguous target net: ' + name)
    return next(iter(matches.values()))


def main():
    from openroad import Tech, Design
    physical = Path('runs/stock-official-baseline')
    sources = list(physical.glob('*-openroad-stamidpnr-3/state_out.json'))
    if len(sources) != 1:
        raise ValueError('Missing final native source')
    state = json.loads(sources[0].read_text())
    paths = [sources[0]] + [Path(state[k]) for k in ('odb', 'def', 'nl', 'pnl', 'sdc')]
    def hashes():
        return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    before = hashes()
    log = (Path(state['odb']).parent/'openroad-resizertimingpostgrt.log').read_text()
    totals = re.findall(r'(?m)^Total\s+\d+\s+\d+\s+[0-9.]+%\s+\d+\s*/\s*\d+\s*/\s*(\d+)\s*$', log)
    if not totals:
        raise ValueError('Missing final live congestion reference')
    tech = Tech()
    design = Design(tech)
    design.readDb(state['odb'])
    db = tech.getDB()
    block = db.getChip().getBlock()
    grid = block.getGCellGrid()
    if grid is None:
        raise ValueError('Missing saved native congestion grid')
    layers = [db.getTech().findLayer(n) for n in ('Metal2', 'Metal3', 'Metal4')]
    if any(layer is None for layer in layers):
        raise ValueError('Missing signal routing layer')
    overflow = saved_overflow(grid, layers)
    if sum(r['overflow'] for r in overflow) != int(totals[-1]):
        raise ValueError('Saved congestion differs from final live report; refuse spatial inference')
    antenna_root = Path('runs/stock-corner-audit/fresh-antenna')
    reports = list(antenna_root.glob('*-openroad-checkantennas/reports/antenna.rpt'))
    if len(reports) != 1:
        raise ValueError('Missing final antenna report')
    names = re.findall(r'^Net: (\S+)\s*$', reports[0].read_text(), re.M)
    if len(names) != len(set(names)):
        raise ValueError('Duplicate antenna target')
    targets = ['u_chip.g_lane[1].u_slots.g_word[51].dec'] + names
    # The source drive experiment can place a buffer between dec and GATE.
    # Resolve the actual gate input as well, rather than assuming direct wiring.
    icg_name = 'u_chip.g_lane[1].u_slots.g_word[51].u_icg'
    instances = [inst for inst in block.getInsts()
                 if inst.getName().replace(r'\[', '[').replace(r'\]', ']') == icg_name]
    if len(instances) != 1:
        raise ValueError('Missing unique tracked word-enable gate')
    term = instances[0].findITerm('GATE')
    if term is None or term.getNet() is None:
        raise ValueError('Missing tracked gate input net')
    targets.append(term.getNet().getName())
    nets = []
    seen = set()
    for name in dict.fromkeys(targets):
        net = find_net(block, name)
        if net.getName() in seen:
            continue
        seen.add(net.getName())
        pins = []
        for term in net.getITerms():
            inst, port = term.getInst(), term.getMTerm()
            pins.append(dict(instance=inst.getName(), pin=port.getName(),
                             direction=str(port.getIoType()), master=inst.getMaster().getName(),
                             origin_dbu=list(inst.getLocation()), orientation=str(inst.getOrient())))
        nets.append(dict(requested=name, actual_name=net.getName(), signal_type=str(net.getSigType()), pins=pins))
    if hashes() != before:
        raise ValueError('Read-only probe changed source bytes')
    output = Path('runs/portable-geometry')
    output.mkdir(exist_ok=False)
    (output/'saved_geometry.json').write_text(json.dumps(dict(
        source_state=str(sources[0]), source_view_hashes=before,
        units_per_micron=block.getDbUnitsPerMicron(), overflow_edges=overflow,
        final_live_overflow=int(totals[-1]), target_nets=nets,
        physical_changes_applied=False, router_initialized=False,
        official_gds_qualified=False), indent=2)+'\n')


if __name__ == '__main__':
    main()

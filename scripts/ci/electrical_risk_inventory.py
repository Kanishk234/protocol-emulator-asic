"""Select reviewed electrical-risk classes from paired measurements and real topology."""
from combined_physical_plan import connections
from event_nor2_screen import logical_cells
from postgrt_timing import CORNERS


def inventory(summary, netlist, layout):
    if summary.get('source_run') != 38689478738 or summary.get('read_only') is not True:
        raise ValueError('Wrong margin evidence source')
    corners = summary['stages']['screen']
    if set(corners) != set(CORNERS):
        raise ValueError('Incomplete margin corners')
    nets, _ = connections(layout, True)
    cells = {n.strip().removeprefix('\\'): v for n,v in logical_cells(netlist).items()}
    risk = {}
    for data in corners.values():
        for net, rows in data['nets'].items():
            for kind in ('slew', 'capacitance'):
                ratio = rows.get(kind, {}).get('utilization')
                if ratio is not None and ratio >= .45:
                    risk.setdefault(net, set()).add(kind)
    for net, terms in nets.items():
        if len(terms)-1 >= 8 and any(cells.get(n, ('',))[0] == 'sg13cmos5l_antennanp' for n,p in terms):
            risk.setdefault(net, set()).add('fanout')
    skipped = {}
    for net in list(risk):
        terms = nets[net]
        if any(pin in ('CLK', 'GCLK', 'GATE', 'RESET_B') for _,pin in terms):
            skipped[net] = sorted(risk.pop(net))
            continue
        drivers = [(n,p) for n,p in terms if p in ('X','Y','Q')]
        if len(drivers) != 1 or any(n == 'PIN' for n,p in terms):
            raise ValueError('Unreviewed preventive source driver or exposed pin')
    return dict(sources={n:sorted(v) for n,v in sorted(risk.items())},
                protected_sources=skipped, estimated_maximum_utilization=.45)

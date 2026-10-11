"""Map complete electrical reports to actual netlist loads; no physical ECO."""
import argparse
import hashlib
import json
from pathlib import Path
from electrical_report import audit
from event_nor2_screen import logical_cells


def inspect(netlist, report):
    electrical = audit(report)
    cells = logical_cells(netlist)
    branches = []
    for row in electrical['violations']['fanout']:
        pin = row.split()[0]
        name, port = pin.rsplit('/', 1)
        if name not in cells or port not in dict(cells[name][1]):
            raise ValueError('Reported fanout driver absent from exact netlist: ' + pin)
        net = dict(cells[name][1])[port]
        sinks = sorted((n, p) for n, (_, pins) in cells.items()
                       for p, v in pins if v == net and (n, p) != (name, port))
        diodes = [s for s in sinks if cells[s[0]][0] == 'sg13cmos5l_antennanp']
        clocks = name.startswith(('clkbuf', 'delaybuf')) or any(p in ('CLK', 'GCLK', 'GATE') for n, p in sinks)
        branches.append(dict(driver=pin, net=net, master=cells[name][0],
                             actual_sink_pins=len(sinks), diode_pins=len(diodes),
                             other_pins=len(sinks)-len(diodes), sinks=sinks,
                             clock_branch=clocks))
    return dict(netlist_sha256=hashlib.sha256(netlist.encode()).hexdigest(),
                counts=electrical['counts'], branches=branches,
                slew_rows=electrical['violations']['slew'],
                capacitance_rows=electrical['violations']['capacitance'],
                physical_change_applied=False, official_signoff=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('netlist', type=Path)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.netlist.read_text(), args.report.read_text()), indent=2))

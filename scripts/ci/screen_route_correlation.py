"""Explain routed electrical failures against a screened checkpoint; never qualifies it."""
import argparse
import hashlib
import json
from pathlib import Path
from combined_physical_plan import connections
from electrical_report import audit
from event_nor2_screen import logical_cells, validate_antenna_only_changes


def compare(before_nl, before_def, after_nl, after_def, checks):
    validate_antenna_only_changes(before_nl, after_nl)
    old_nets, old_attached = connections(before_def, True)
    new_nets, new_attached = connections(after_def, True)
    old_cells = {n.strip().removeprefix('\\'): c for n, c in logical_cells(before_nl).items()}
    new_cells = {n.strip().removeprefix('\\'): c for n, c in logical_cells(after_nl).items()}
    failures = {}
    if not checks:
        raise ValueError('Missing extracted electrical reports')
    for corner, text in checks.items():
        if corner not in text:
            raise ValueError('Wrong report corner')
        for kind, rows in audit(text)['violations'].items():
            for row in rows:
                name, pin = row.split()[0].rsplit('/', 1)
                terminal = (name, pin)
                net = new_attached[terminal]
                if old_attached.get(terminal) != net:
                    raise ValueError('Failure terminal changed source net')
                failures.setdefault(net, []).append(dict(corner=corner, kind=kind, row=row))
    results = []
    for net, rows in sorted(failures.items()):
        old, new = set(old_nets[net]), set(new_nets[net])
        if old - new:
            raise ValueError('Existing DEF connection removed')
        added = sorted(new - old)
        for name, pin in added:
            if name in old_cells or new_cells[name][0] != 'sg13cmos5l_antennanp' or pin != 'A':
                raise ValueError('Unreviewed added DEF terminal')
        drivers = [p for p in old if p[1] in ('X', 'Y', 'Q') or p[1].startswith('A_DOUT[')]
        if len(drivers) != 1:
            raise ValueError('Missing unique audited driver')
        results.append(dict(net=net, driver='/'.join(drivers[0]),
            before_loads=len(old)-1, after_loads=len(new)-1,
            added_diodes=[name for name, _ in added],
            connectivity_unchanged=old == new, violations=rows))
    return dict(nets=results, antenna_only_netlist_changes_audited=True,
                official_signoff=False,
                input_sha256={name: hashlib.sha256(text.encode()).hexdigest()
                    for name, text in dict(before_nl=before_nl, before_def=before_def,
                                           after_nl=after_nl, after_def=after_def).items()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('before_nl', 'before_def', 'after_nl', 'after_def'):
        parser.add_argument(name, type=Path)
    parser.add_argument('--checks', action='append', required=True, type=Path,
                        help='checks.rpt whose parent directory is the corner name')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    checks = {p.parent.name: p.read_text() for p in args.checks}
    if len(checks) != len(args.checks):
        raise ValueError('Duplicate report corner')
    result = compare(*(getattr(args, n).read_text() for n in
                       ('before_nl', 'before_def', 'after_nl', 'after_def')), checks)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

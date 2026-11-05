"""Measure direct receiver protection and native preservation; no closure claim."""
import argparse
import json
from pathlib import Path
import re
from guarded_word_probe import logged_objects


def connections(text):
    cells = {}
    for master, name, body in re.findall(r'\b(sg13cmos5l_\w+)\s+(\S+)\s*\((.*?)\);', text, re.S):
        name = name.lstrip('\\')
        if name in cells:
            raise ValueError('Duplicate cell')
        cells[name] = (master, {p: n.strip().lstrip('\\') for p, n in re.findall(r'\.(\w+)\s*\((.*?)\)', body, re.S)})
    preserved = []
    objects = set()
    for name, (master, pins) in cells.items():
        if not name.endswith('.trw_receiver_sink'):
            continue
        prefix = name.removesuffix('trw_receiver_sink')
        diode = cells.get(prefix + 'trw_receiver_diode')
        if master != 'sg13cmos5l_buf_2' or not diode or diode[0] != 'sg13cmos5l_antennanp':
            continue
        if diode[1].get('A') != pins.get('A'):
            continue
        preserved.append(name)
        objects.update({('Instance', name), ('Instance', prefix + 'trw_receiver_diode'), ('Net', pins['A'])})
    return preserved, objects


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    parser.add_argument('--protected', choices=['true', 'false'], required=True)
    args = parser.parse_args()
    files = list(args.root.glob('*-openroad-resizertimingpostgrt/tt_um_tripwire.nl.v'))
    if len(files) != 1:
        raise ValueError('Missing final native netlist')
    preserved, objects = connections(files[0].read_text())
    covered = []
    for stage in ('repairdesignpostgpl', 'resizertimingpostcts', 'repairdesignpostgrt', 'resizertimingpostgrt'):
        logs = list(args.root.glob(f'*-openroad-{stage}/openroad-{stage}.log'))
        if len(logs) == 1 and objects and objects <= logged_objects(logs[0].read_text()):
            covered.append(stage)
    result = dict(protected=args.protected, direct_receiver_connections=len(preserved),
                  native_protection_stages=covered, full_design_qualified=False,
                  lower_layer_protection_proven=False)
    (args.root / 'receiver_result.json').write_text(json.dumps(result, indent=2) + '\n')
    if args.protected == 'true' and (len(preserved) != 7 or len(covered) != 4):
        raise ValueError('Receiver protection not preserved through all native stages')


if __name__ == '__main__':
    main()

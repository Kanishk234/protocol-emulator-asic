"""Measure controlled toy antenna response; never qualify TRIPWIRE."""
import argparse
import json
from pathlib import Path
import re


def sink_violation(report):
    for net in re.split(r'(?=^Net:)', report, flags=re.M):
        if not re.match(r'Net:\s+trw_ap_node\s*\n', net):
            continue
        for pin in re.split(r'(?=^  Pin:)', net, flags=re.M):
            if re.match(r'  Pin:\s+trw_ap_sink/A\s', pin):
                return '(VIOLATED)' in pin
    return False


def separation(def_text):
    dbu = int(re.search(r'UNITS DISTANCE MICRONS (\d+)', def_text).group(1))
    components = def_text.split('COMPONENTS ', 1)[1].split('END COMPONENTS', 1)[0]
    positions = []
    for name in ('trw_ap_driver', 'trw_ap_sink'):
        block = re.search(r'(?m)^\s*- ' + name + r'\s+.*?;', components, re.S)
        if block is None:
            raise ValueError('Missing relay placement: ' + name)
        match = re.search(r'\+ (?:PLACED|FIXED) \( (\d+) (\d+) \)', block.group())
        if match is None:
            raise ValueError('Unplaced relay')
        positions.append(tuple(int(v) / dbu for v in match.groups()))
    return sum(abs(a - b) for a, b in zip(*positions))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('physical', type=Path)
    p.add_argument('antenna', type=Path)
    p.add_argument('--diode-present', choices=['true', 'false'], required=True)
    args = p.parse_args()
    def one(root, pattern):
        paths = list(root.glob(pattern))
        if len(paths) != 1:
            raise ValueError('Missing unique evidence: ' + pattern)
        return paths[0]
    config = json.loads((args.physical / 'resolved.json').read_text())
    if (config['RUN_ANTENNA_REPAIR'] or config['RUN_HEURISTIC_DIODE_INSERTION']
            or config['DIODE_ON_PORTS'] != 'none'):
        raise ValueError('Automatic antenna repair invalidates this control')
    distance = separation(one(args.physical, '*-openroad-resizertimingpostgrt/*.def').read_text())
    if distance < 400:
        raise ValueError('Relay separation collapsed; insufficient controlled geometry')
    violated = sink_violation(one(args.antenna, '*/reports/antenna.rpt').read_text())
    metrics = json.loads(one(args.antenna, '*/or_metrics_out.json').read_text())
    present = args.diode_present == 'true'
    result = dict(diode_present=present, source_sink_origin_separation_um=distance,
                  relay_sink_antenna_violation=violated,
                  expected_response_observed=violated != present,
                  fresh_antenna={k: metrics[k] for k in ('antenna__violating__nets', 'antenna__violating__pins')},
                  full_design_qualification=False,
                  scope='Toy response measurement; pair comparison required to establish efficacy')
    (args.physical / 'antenna_efficacy.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

"""Measure a tiny stock-flow probe; never qualify the full design."""
import argparse
import json
from pathlib import Path
import re


def connectivity(text):
    cells = {name: (master, dict(re.findall(r'\.(\w+)\s*\(\s*([^)]*?)\s*\)', body)))
             for master, name, body in re.findall(
                 r'\b(sg13cmos5l_\w+)\s+(\S+)\s*\((.*?)\);', text, re.S)}
    expected = {'trw_ap_driver': 'sg13cmos5l_buf_2',
                'trw_ap_sink': 'sg13cmos5l_buf_2',
                'trw_ap_diode': 'sg13cmos5l_antennanp'}
    if any(name not in cells or cells[name][0] != master for name, master in expected.items()):
        return False
    node = cells['trw_ap_driver'][1].get('X')
    return bool(node and node == cells['trw_ap_sink'][1].get('A')
                == cells['trw_ap_diode'][1].get('A'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--protected', choices=['true', 'false'], required=True)
    args = parser.parse_args()
    paths = list(args.root.glob('*-openroad-resizertimingpostgrt/*.nl.v'))
    if len(paths) != 1:
        raise ValueError('Missing unique final native netlist')
    intact = connectivity(paths[0].read_text())
    logs = list(args.root.glob('*-openroad-*/openroad-*.log'))
    matches = [str(p.relative_to(args.root)) for p in logs
               if "matched don't touch regular expression" in p.read_text()]
    protected = args.protected == 'true'
    required_stages = ('repairdesignpostgpl', 'resizertimingpostcts',
                       'repairdesignpostgrt', 'resizertimingpostgrt')
    covered = all(any(('-openroad-' + stage + '/') in name for name in matches)
                  for stage in required_stages)
    metric_paths = list(args.root.glob('*-openroad-stamidpnr-3/or_metrics_out.json'))
    if len(metric_paths) != 1:
        raise ValueError('Missing unique final native STA metrics')
    raw = json.loads(metric_paths[0].read_text())
    if not any(k.startswith('timing__setup__ws__corner:') for k in raw):
        raise ValueError('Missing fresh native setup measurement')
    result = dict(protected=protected, connectivity_preserved=intact,
                  native_protection_logs=matches, full_design_qualification=False,
                  all_repair_stages_exercised_protection=covered,
                  final_native_metrics={k: v for k, v in raw.items()
                                        if k.startswith(('timing__', 'design__max_'))},
                  extracted_timing_performed=False,
                  scope='Tiny stock Classic probe; metrics are measurements, not design acceptance')
    (args.root / 'probe_result.json').write_text(json.dumps(result, indent=2) + '\n')
    if protected and (not intact or not covered):
        raise ValueError('Protected node not preserved or native protection not exercised')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

"""Read-only connectivity classification of native marker memberships.

Groups overlap. Membership is neither routing demand nor causal attribution.
Native planar marker overflow is distinct from final per-layer GRT overflow.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from audit_congestion_report import audit as marker_audit
from cloud_cfg_fanout import parse_census


def classify(endpoints):
    groups = set()
    if any(name.endswith('/L_HI') or name.endswith('/L_LO') for name, _ in endpoints):
        groups.add('tie_driven')
    if any(name.startswith('u_fabric/') for name, _ in endpoints):
        groups.add('fabric_boundary')
    if any(name.startswith(('clkbuf_', 'delaybuf_', 'clkload')) for name, _ in endpoints):
        groups.add('clock_tree')
    if any(name.startswith('u_shell.u_crc.') for name, _ in endpoints):
        groups.add('crc_shell')
    if any(name.startswith('u_shell.u_spi.') for name, _ in endpoints):
        groups.add('spi_shell')
    if any(name.startswith('u_cfg.') for name, _ in endpoints):
        groups.add('configuration_controller')
    if any(name.startswith('fanout') for name, _ in endpoints):
        groups.add('fanout_repair_branch')
    if not groups:
        groups.add('other')
    return groups


def audit(census, report, digest):
    _, pins = parse_census(census.read_text())
    nets = defaultdict(list)
    for key, value in pins.items():
        if key[0] == 'PIN':
            nets[value[-1].replace('\\', '')].append((key[1], value[0]))
    native = marker_audit(report, digest)
    by_group = defaultdict(set)
    counts = Counter()
    memberships = defaultdict(set)
    missing = set()
    for index, marker in enumerate(native['markers']):
        for name in set(marker['source_nets_native']):
            name = name.replace('\\', '')
            if name not in nets:
                missing.add(name)
                continue
            counts[name] += 1
            memberships[name].add(index)
            for group in classify(nets[name]):
                by_group[group].add(index)
    if missing:
        raise ValueError('Native marker nets absent in census: ' + repr(sorted(missing)))
    tie_markers = by_group['tie_driven']
    return {
        'scope': 'overlapping native marker memberships, not causal routing attribution',
        'census_sha256': hashlib.sha256(census.read_bytes()).hexdigest(),
        'report_sha256': native['source_sha256'],
        'marker_count': native['marker_count'],
        'group_marker_counts_overlap': {k: len(v) for k, v in sorted(by_group.items())},
        'markers_without_any_tie_driven_net': native['marker_count'] - len(tie_markers),
        'ranked_nets': [dict(net=n, markers=count, groups=sorted(classify(nets[n])),
                             endpoints=nets[n]) for n, count in sorted(counts.items(), key=lambda x: (-x[1], x[0]))],
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('census', type=Path)
    parser.add_argument('report', type=Path)
    parser.add_argument('--sha256', required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.census, args.report, args.sha256), indent=2))

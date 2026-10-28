"""Enforce the existing pre-DRT gates on fresh, source-bound stock measurements."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

from postgrt_timing import CORNERS


def one(root, pattern):
    paths = list(root.glob(pattern))
    if len(paths) != 1:
        raise ValueError(f'Expected one {pattern}, found {len(paths)}')
    return paths[0]


def qualify(physical, audit):
    physical, audit = Path(physical), Path(audit)
    receipt = json.loads((audit / 'read_only_audit.json').read_text())
    source = one(physical, '*-openroad-stamidpnr-3/state_out.json')
    if Path(receipt['source_state']).resolve() != source.resolve():
        raise ValueError('Qualification source is not the final checkpoint')
    state = json.loads(source.read_text())
    paths = [source] + [Path(state[key]) for key in ('odb', 'def', 'nl', 'pnl', 'sdc')]
    hashes = receipt['unchanged_physical_view_hashes']
    if set(hashes) != {str(path) for path in paths}:
        raise ValueError('Incomplete source-view hash receipt')
    for path in paths:
        if not path.resolve().is_relative_to(physical.resolve()):
            raise ValueError('Physical view outside the source run')
        if hashlib.sha256(path.read_bytes()).hexdigest() != hashes[str(path)]:
            raise ValueError('Physical source changed after audit')
    if set(receipt['fresh_corner_metrics']) != set(CORNERS):
        raise ValueError('Missing or unexpected audit corner')
    failures = []
    for corner in CORNERS:
        row = receipt['fresh_corner_metrics'][corner]
        expected = [f'timing__{kind}__ws__corner:{corner}' for kind in ('setup', 'hold')]
        expected += [f'design__max_{kind}_violation__count__corner:{corner}'
                     for kind in ('slew', 'cap', 'fanout')]
        if set(row) != set(expected):
            raise ValueError('Incomplete timing/electrical receipt')
        for stage in ('before-', 'after-'):
            raw = json.loads(one(audit / (stage + corner), '*-openroad-stamidpnr/or_metrics_out.json').read_text())
            for key in expected:
                value = row[key]
                if (type(value) not in (int, float) or not math.isfinite(value)
                        or type(raw.get(key)) not in (int, float) or raw.get(key) != value):
                    raise ValueError('Fresh raw timing/electrical metric mismatch')
        for kind in ('setup', 'hold'):
            key = f'timing__{kind}__ws__corner:{corner}'
            minimum = 0.05 if kind == 'hold' and corner == CORNERS[0] else 0
            if row[key] < minimum:
                failures.append(f'{corner} {kind}: {row[key]} ns < {minimum} ns')
        for kind in ('slew', 'cap', 'fanout'):
            value = row[f'design__max_{kind}_violation__count__corner:{corner}']
            if type(value) is not int or value < 0:
                raise ValueError('Invalid electrical violation count')
            if value:
                failures.append(f'{corner} {kind}: {value}')
    antenna = receipt['fresh_antenna_metrics']
    keys = ('antenna__violating__nets', 'antenna__violating__pins')
    if set(antenna) != set(keys):
        raise ValueError('Incomplete antenna receipt')
    raw = json.loads(one(audit / 'fresh-antenna', '*-openroad-checkantennas/or_metrics_out.json').read_text())
    for key in keys:
        value = antenna[key]
        if type(value) is not int or value < 0 or type(raw.get(key)) is not int or raw.get(key) != value:
            raise ValueError('Fresh raw antenna metric mismatch')
        if value:
            failures.append(f'{key}: {value}')
    log = one(physical, '*-openroad-resizertimingpostgrt/openroad-resizertimingpostgrt.log')
    if Path(state['odb']).resolve().parent != log.resolve().parent:
        raise ValueError('Routing evidence is not from the final physical checkpoint')
    totals = re.findall(r'(?m)^Total\s+\d+\s+\d+\s+[0-9.]+%\s+\d+\s*/\s*\d+\s*/\s*(\d+)\s*$', log.read_text())
    if not totals:
        raise ValueError('Missing final global-routing overflow report')
    overflow = int(totals[-1])
    if overflow:
        failures.append(f'final global-routing overflow: {overflow}')
    return dict(qualified=not failures, failures=failures,
                final_global_overflow=overflow, source_state=str(source),
                minimum_fast_hold_ns=0.05, detailed_routing_performed=False,
                official_gds_signoff=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--physical', type=Path, required=True)
    parser.add_argument('--audit', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = qualify(args.physical, args.audit)
    except (ValueError, KeyError, OSError) as error:
        result = dict(qualified=False, failures=[str(error)])
    (args.audit / 'screen_qualification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    if not result['qualified']:
        raise SystemExit('Final screen gates fail; measurements remain in the uploaded artifact')


if __name__ == '__main__':
    main()

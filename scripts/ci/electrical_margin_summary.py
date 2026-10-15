"""Parse complete per-net electrical checks, including legal near-limit rows."""
import math
import re
from postgrt_timing import CORNERS

NUMBER = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'
ROW = re.compile(r'^(\S+)\s+('+NUMBER+r')\s+('+NUMBER+r')(?:\s+('+NUMBER+r'))?(?:\s+\((?:MET|VIOLATED)\))?\s*$')


def parse(text):
    lines = text.splitlines()
    begin = [x.split() for x in lines if x.startswith('TRIPWIRE_MARGIN_BEGIN ')]
    end = [x.split() for x in lines if x.startswith('TRIPWIRE_MARGIN_END ')]
    if len(begin) != 1 or len(end) != 1 or begin[0][1] != end[0][1] or begin[0][1] not in CORNERS:
        raise ValueError('Missing or mismatched margin completion')
    corner = begin[0][1]
    nets = {}; current = None; kind = None
    for line in lines:
        if line.startswith('TRIPWIRE_NET_HEX '):
            current = bytes.fromhex(line.split()[1]).decode()
            if current in nets:
                raise ValueError('Duplicate margin net')
            nets[current] = {}; kind = None
        match = re.fullmatch(r'max (slew|fanout|capacitance)', line.strip())
        if match:
            kind = match[1]
        match = ROW.fullmatch(line.strip()) if kind and current else None
        if match:
            pin, limit, actual = match[1], float(match[2]), float(match[3])
            if not all(math.isfinite(x) for x in (limit, actual)) or limit < 0 or actual < 0:
                raise ValueError('Invalid electrical margin measurement')
            ratio = actual/limit if limit else (None if actual == 0 else float('inf'))
            if ratio is not None and not math.isfinite(ratio):
                raise ValueError('Nonfinite electrical utilization')
            row = dict(pin=pin, limit=limit, actual=actual, utilization=ratio)
            old = nets[current].get(kind)
            if old is None or (ratio or 0) > (old['utilization'] or 0):
                nets[current][kind] = row
    if len(nets) != int(end[0][2]) or not nets or not any(nets.values()):
        raise ValueError('Incomplete or empty per-net margin coverage')
    counts = {k: sum(v.get(k, {}).get('utilization') is not None and
                     v[k]['utilization'] >= .9 for v in nets.values())
              for k in ('slew', 'fanout', 'capacitance')}
    return corner, dict(net_count=len(nets), near_limit_threshold=.9,
                        near_limit_counts=counts, nets=nets)


def summarize(paths):
    result = {}
    for p in paths:
        corner, data = parse(p.read_text())
        if corner in result:
            raise ValueError('Duplicate margin corner')
        result[corner] = data
    if set(result) != set(CORNERS):
        raise ValueError('Incomplete corner set')
    return result


def paired(screen, extracted):
    if set(screen) != set(CORNERS) or set(extracted) != set(CORNERS):
        raise ValueError('Paired probe requires all corners')
    result = {}
    for corner in CORNERS:
        before, after = screen[corner]['nets'], extracted[corner]['nets']
        rows = []
        for net in sorted(before.keys() & after.keys()):
            for kind in sorted(before[net].keys() & after[net].keys()):
                a, b = before[net][kind], after[net][kind]
                if a['limit'] != b['limit']:
                    raise ValueError('Paired electrical limit changed')
                if a['utilization'] is None or b['utilization'] is None:
                    continue
                rows.append(dict(net=net, kind=kind, screen=a['utilization'],
                    extracted=b['utilization'], drift=b['utilization']-a['utilization']))
        if not rows:
            raise ValueError('No matched electrical measurements')
        result[corner] = dict(matched_nets=len(before.keys() & after.keys()),
            screen_only_nets=len(before.keys()-after.keys()),
            extracted_only_nets=len(after.keys()-before.keys()),
            newly_failing=[r for r in rows if r['screen'] <= 1 < r['extracted']],
            largest_drift=sorted(rows, key=lambda r: (-r['drift'], r['net'], r['kind']))[:100])
    return result

"""Summarize bounded FF hold reports without asserting endpoint completeness."""
import hashlib
import re


def summarize(path, corner):
    text = path.read_text()
    begin = f'TRIPWIRE_HOLD_FRONTIER_BEGIN {corner} 0.05 100000'
    end = f'TRIPWIRE_HOLD_FRONTIER_END {corner}'
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError('Missing or repeated hold-frontier boundary/corner')
    if text.index(begin) > text.index(end):
        raise ValueError('Reversed hold-frontier boundaries')
    body = text.split(begin, 1)[1].split(end, 1)[0]
    paths = []
    for block in re.split(r'(?m)^Startpoint: ', body)[1:]:
        start = re.match(r'([^\n]+)', block)
        endpoint = re.search(r'(?m)^Endpoint: ([^\n]+)', block)
        slack = re.findall(r'(?m)^\s*(-?\d+(?:\.\d+)?)\s+slack\s+\((?:MET|VIOLATED)\)\s*$', block)
        if not start or not endpoint or len(slack) != 1 or not re.search(r'(?m)^Path Type: min\s*$', block):
            raise ValueError('Incomplete or non-min hold path')
        value = float(slack[0])
        if value > 0.0500005:
            raise ValueError('Path outside requested hold frontier')
        paths.append(dict(startpoint=start[1], endpoint=endpoint[1], slack_ns=value,
                          reserve_shortfall_ns=round(max(0, 0.05 - value), 6)))
    if not paths and 'No paths found.' not in body:
        raise ValueError('Empty report without explicit no-path result')
    return dict(corner=corner, report=str(path), report_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                scope='Reported FF min paths only; not proof of exhaustive endpoint coverage',
                exhaustive_endpoint_coverage_claimed=False, requested_paths_per_group=100000,
                reported_paths=len(paths), reported_endpoints=len({p['endpoint'] for p in paths}),
                reported_negative_paths=sum(p['slack_ns'] < 0 for p in paths),
                reported_below_reserve=sum(p['slack_ns'] < 0.05 for p in paths), paths=paths)

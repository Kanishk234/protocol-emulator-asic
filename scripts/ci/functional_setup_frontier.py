"""Read actual flop/output path slack; never infer margin from clamped WNS."""
import math
import re


def parse_report(text, corner):
    if f'TRIPWIRE_FUNCTIONAL_SETUP {corner}' not in text:
        raise ValueError('Missing exact-corner functional timing report')
    counts = {}
    for label in ('FLOP_DATA_ENDPOINTS', 'OUTPUT_ENDPOINTS'):
        values = re.findall(r'^'+label+r' (\d+)\s*$', text, re.M)
        if len(values) != 1:
            raise ValueError('Missing or repeated endpoint inventory')
        counts[label] = int(values[0])
    if counts['FLOP_DATA_ENDPOINTS'] == 0:
        raise ValueError('Missing flop endpoints')
    rows = re.findall(r'^\s*(\S+)\s+slack \((?:MET|VIOLATED)\)\s*$', text, re.M)
    if not rows:
        raise ValueError('No actual reported path slack')
    slacks = [float(value) for value in rows]
    if any(not math.isfinite(value) for value in slacks):
        raise ValueError('Nonfinite path slack')
    return dict(corner=corner, worst_reported_setup_slack_ns=min(slacks),
                reported_paths=len(slacks), endpoint_inventory=counts,
                scope='Flop/output path reports only; ordinary all-endpoint checks still required',
                official_signoff=False)

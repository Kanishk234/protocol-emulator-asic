"""Conservative screen-only margin gate; final signoff constraints remain unchanged."""
import json
from pathlib import Path
from electrical_margin_summary import summarize


def measure(reports):
    corners = summarize(reports)
    maximum = {}; counts = {}; offenders = {}
    for corner, data in corners.items():
        maximum[corner] = {}
        counts[corner] = {}
        offenders[corner] = {}
        for kind in ('slew', 'capacitance'):
            values = [v[kind]['utilization'] for v in data['nets'].values()
                      if kind in v and v[kind]['utilization'] is not None]
            if not values:
                raise ValueError('Missing conservative electrical margin measurements')
            maximum[corner][kind] = max(values)
            counts[corner][kind] = sum(v > .45 for v in values)
            offenders[corner][kind] = sorted(
                [dict(net=net, **rows[kind]) for net,rows in data['nets'].items()
                 if kind in rows and rows[kind]['utilization'] is not None
                 and rows[kind]['utilization'] > .45],
                key=lambda row: (-row['utilization'], row['net']))
    passed = not any(n for row in counts.values() for n in row.values())
    return dict(estimated_margin_limit=.45, estimated_margin_maximum=maximum,
                estimated_margin_exceedances=counts, estimated_margin_offenders=offenders,
                estimated_margin_pass=passed)


def enforce(root):
    root = Path(root)
    path = root/'gates.json'
    receipt = json.loads(path.read_text())
    qualified = receipt['qualified']
    receipt['qualified'] = False
    path.write_text(json.dumps(receipt, indent=2)+'\n')
    reports = list((root/'timing').glob('after-*/*-openroad-stamidpnr/electrical_margin.rpt'))
    result = measure(reports)
    receipt.update(result, qualified=qualified and result['estimated_margin_pass'])
    path.write_text(json.dumps(receipt, indent=2)+'\n')
    if not result['estimated_margin_pass']:
        print('TRIPWIRE conservative margin offenders: '+json.dumps(result['estimated_margin_offenders'],sort_keys=True),flush=True)
        raise ValueError('Conservative global electrical screen margin fails; no DRT')

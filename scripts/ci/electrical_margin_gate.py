"""Conservative screen-only margin gate; final signoff constraints remain unchanged."""
import json
from pathlib import Path
from electrical_margin_summary import summarize


def enforce(root):
    root = Path(root)
    path = root/'gates.json'
    receipt = json.loads(path.read_text())
    qualified = receipt['qualified']
    receipt['qualified'] = False
    path.write_text(json.dumps(receipt, indent=2)+'\n')
    reports = list((root/'timing').glob('after-*/*-openroad-stamidpnr/electrical_margin.rpt'))
    corners = summarize(reports)
    maximum = {}; counts = {}
    for corner, data in corners.items():
        maximum[corner] = {}
        counts[corner] = {}
        for kind in ('slew', 'capacitance'):
            values = [v[kind]['utilization'] for v in data['nets'].values()
                      if kind in v and v[kind]['utilization'] is not None]
            if not values:
                raise ValueError('Missing conservative electrical margin measurements')
            maximum[corner][kind] = max(values)
            counts[corner][kind] = sum(v > .45 for v in values)
    passed = not any(n for row in counts.values() for n in row.values())
    receipt.update(estimated_margin_limit=.45, estimated_margin_maximum=maximum,
                   estimated_margin_exceedances=counts, estimated_margin_pass=passed,
                   qualified=qualified and passed)
    path.write_text(json.dumps(receipt, indent=2)+'\n')
    if not passed:
        raise ValueError('Conservative global electrical screen margin fails; no DRT')

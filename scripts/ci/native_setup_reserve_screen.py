"""Require measured setup headroom before routing the native wire150 recipe."""
import json
import math
from pathlib import Path
import re

from native_margin_screen import main as margin_screen
from native_wire150_screen import configure as wire_configure
from postgrt_timing import CORNERS

MINIMUM_SLOW_CAPTURE_SETUP_NS = 3.5


def configure(config):
    result = wire_configure(config)
    if result['GRT_RESIZER_SETUP_SLACK_MARGIN'] != 0:
        raise ValueError('Unexpected native wire150 setup policy')
    result['GRT_RESIZER_SETUP_SLACK_MARGIN'] = 4.0
    return result


def capture_setup(report):
    blocks = report.split('Startpoint: ')[1:]
    if not blocks:
        raise ValueError('Missing FF capture setup paths')
    values = []
    for block in blocks:
        endpoint = re.findall(r'^Endpoint: .+$', block, re.M)
        slack = re.findall(r'^\s*([-+\d.eE]+)\s+slack \((?:MET|VIOLATED)\)\s*$', block, re.M)
        if (len(endpoint) != 1 or 'edge-triggered flip-flop' not in endpoint[0]
                or not re.search(r'^Path Type: max\s*$', block, re.M) or len(slack) != 1):
            raise ValueError('Incomplete or wrong FF capture setup report')
        value = float(slack[0])
        if not math.isfinite(value):
            raise ValueError('Nonfinite FF capture setup slack')
        values.append(value)
    return min(values)


def enforce(root):
    path = root/'gates.json'
    receipt = json.loads(path.read_text())
    prior_qualified = receipt['qualified']
    # Persist failure before reading evidence: missing/malformed reports fail closed.
    receipt.update(qualified=False, minimum_slow_capture_setup_ns=MINIMUM_SLOW_CAPTURE_SETUP_NS)
    path.write_text(json.dumps(receipt, indent=2)+'\n')
    measured = {}
    for corner in CORNERS:
        reports = list((root/'timing'/f'after-{corner}').glob('*-openroad-stamidpnr/capture_setup.rpt'))
        if len(reports) != 1:
            raise ValueError('Missing unique FF capture setup report')
        measured[corner] = capture_setup(reports[0].read_text())
    passed = measured[CORNERS[1]] >= MINIMUM_SLOW_CAPTURE_SETUP_NS
    receipt.update(capture_setup_minimum_ns=measured, estimated_setup_reserve_pass=passed,
                   qualified=prior_qualified and passed)
    path.write_text(json.dumps(receipt, indent=2)+'\n')
    if not receipt['qualified']:
        raise ValueError('Native setup reserve screen fails; no detailed routing')


def main(config_transform=configure):
    margin_screen(config_transform=config_transform, final_antenna_repair=True,
                  audit_tcl=Path('workflow-src/scripts/ci/native_timing_headroom_audit.tcl'))
    enforce(Path('runs/native-stock-screen'))


if __name__ == '__main__':
    main()

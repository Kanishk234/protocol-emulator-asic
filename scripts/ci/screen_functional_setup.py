"""Read repeated stock functional reports alongside ordinary screen checks."""
from pathlib import Path

from extracted_timing import check_stock_report_uncertainty
from functional_setup_frontier import parse_report
from postgrt_timing import CORNERS


def collect(root):
    root = Path(root)
    rows = {}
    for corner in CORNERS:
        repeated = []
        for phase in ('before', 'after'):
            matches = list((root/f'{phase}-{corner}').glob('*-openroad-stamidpnr/functional_setup_frontier.rpt'))
            if len(matches) != 1:
                raise ValueError('Missing or ambiguous functional setup report')
            report = matches[0]
            for name in ('max.rpt', 'min.rpt'):
                check_stock_report_uncertainty((report.parent/name).read_text())
            repeated.append(parse_report(report.read_text(), corner))
        if repeated[0] != repeated[1]:
            raise ValueError('Repeated functional setup report changed')
        rows[corner] = repeated[0]
    return rows

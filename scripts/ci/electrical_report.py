"""Audit OpenSTA checks reports; missing electrical sections are not passes."""
import argparse
import json
from pathlib import Path
import re


def audit(text):
    sections = {}
    current = None
    for line in text.splitlines():
        heading = re.fullmatch(r'max (slew|fanout|capacitance)', line.strip())
        if heading:
            current = heading[1]
            if current in sections:
                raise ValueError('Duplicate electrical section')
            sections[current] = []
        elif line.startswith('==='):
            current = None
        elif '(VIOLATED)' in line and current:
            sections[current].append(line.strip())
    if set(sections) != {'slew', 'fanout', 'capacitance'}:
        raise ValueError('Incomplete electrical report')
    for label, key in [('slew', 'slew'), ('fanout', 'fanout'), ('cap', 'capacitance')]:
        totals = re.findall(r'^max ' + label + r' violation count (\d+)\s*$', text, re.M)
        if totals and (len(totals) != 1 or int(totals[0]) != len(sections[key])):
            raise ValueError('Electrical rows disagree with printed total')
    return {'counts': {key: len(rows) for key, rows in sections.items()},
            'violations': sections,
            'no_reported_electrical_violations': not any(sections.values()),
            'official_signoff': False}


def audit_corners(stage, corners):
    results = {}
    for corner in corners:
        report = stage / corner / 'checks.rpt'
        text = report.read_text()
        if corner not in text:
            raise ValueError('Electrical report corner mismatch')
        results[corner] = audit(text)
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.report.read_text()), indent=2))

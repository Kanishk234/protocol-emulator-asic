"""Package exact exported GDS for independent, unchanged TT precheck.

Classify Magic markers without waiving them or claiming official signoff.
"""
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET

FIXTURES = Path(__file__).parent/'fixtures/wire600_selective'
PROFILE = json.loads((FIXTURES/'mux_precheck.json').read_text())
PREFIX = 'runs/wire600-mux-signoff/'


def classify(text, bounds):
    bounds = tuple(map(Decimal, bounds))
    counts = Counter()
    outside = []
    rule = None
    for line in text.splitlines()[1:]:
        if not line.strip() or line.startswith('---'):
            continue
        if not line.startswith(' '):
            rule = line
            continue
        match = re.fullmatch(r'\s+(-?\d+(?:\.\d+)?)um\s+(-?\d+(?:\.\d+)?)um\s+(-?\d+(?:\.\d+)?)um\s+(-?\d+(?:\.\d+)?)um\s*', line)
        if not match or rule is None:
            raise ValueError('Malformed Magic DRC report')
        box = tuple(map(Decimal, match.groups()))
        x1, y1, x2, y2 = box
        if x1 > x2 or y1 > y2:
            raise ValueError('Reversed DRC rectangle')
        counts[rule] += 1
        if not (bounds[0] <= x1 <= x2 <= bounds[2]
                and bounds[1] <= y1 <= y2 <= bounds[3]):
            outside.append(dict(rule=rule, box_um=list(map(str, box))))
    if not counts:
        raise ValueError('Empty Magic DRC evidence')
    return dict(total=sum(counts.values()), by_rule=dict(counts),
                outside_macro=outside, violation_waiver=False)


def validate(root, run):
    root = Path(root)
    if any(run.get(k) != v for k, v in PROFILE['run'].items()):
        raise ValueError('Wrong exported GDS provenance')
    for name, sha in PROFILE['files'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != sha:
            raise ValueError('Changed exported GDS evidence: '+name)
    audit = classify((root/PREFIX/'05-magic-drc/reports/drc.magic.rpt').read_text(),
                     PROFILE['macro_bbox_um'])
    if audit['total'] != PROFILE['magic_drc_count'] or audit['outside_macro']:
        raise ValueError('Magic marker classification differs from review')
    for stage, metric, expected in (
        ('05-magic-drc', 'magic__drc_error__count', PROFILE['magic_drc_count']),
        ('07-magic-spiceextraction', 'magic__illegal_overlap__count', PROFILE['overlap_count']),
        ('09-netgen-lvs', 'design__lvs_error__count', 0),
    ):
        metrics = json.loads((root/PREFIX/stage/'state_out.json').read_text())['metrics']
        if metrics.get(metric) != expected:
            raise ValueError('Unexpected signoff metric: '+metric)
    # Compare each overlap against the documented Metal4 PDN gap in the FS
    # SRAM view. These classifications are evidence, never a precheck waiver.
    count = classify_overlaps(root/PREFIX/'07-magic-spiceextraction/feedback.xml')
    audit.update(overlap_markers_in_pdn_gap=count, lvs_errors=0,
                 official_signoff=False, precheck_passed=False)
    return audit


def classify_overlaps(path):
    items = list(ET.parse(path).getroot().iter('item'))
    if len(items) != PROFILE['overlap_count']:
        raise ValueError('Wrong overlap feedback count')
    for item in items:
        if item.findtext('category') != "'obsm4-metal4.ILLEGAL_OVERLAP'":
            raise ValueError('Unexpected overlap category')
        polygon = item.findtext('values/value', '')
        coords = [Decimal(v) for v in re.findall(r'-?\d+\.\d+', polygon)]
        if len(coords) != 8 or not polygon.startswith('polygon: '):
            raise ValueError('Malformed overlap polygon')
        xs, ys = coords[::2], coords[1::2]
        if not (Decimal('186.135') <= min(ys) <= max(ys) <= Decimal('192.255')
                and any(c-Decimal('1.05') <= min(xs) <= max(xs) <= c+Decimal('1.05')
                        for c in map(Decimal, ('29.24', '96.68', '164.12', '231.56')))):
            raise ValueError('Overlap outside reviewed PDN obstruction gap')
    return len(items)


def package(root, run, output):
    audit = validate(root, run)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    submission = output/'tt_submission'
    submission.mkdir()
    for key, suffix in (('gds', '.gds'), ('lef', '.lef')):
        shutil.copyfile(Path(root)/PROFILE[key], submission/('tt_um_tripwire'+suffix))
    shutil.copyfile(FIXTURES/'mux_submission_info.yaml', output/'info.yaml')
    (submission/'pdk.json').write_text(json.dumps({'PDK': 'ihp-sg13cmos5l'})+'\n')
    (output/'diagnostic_identity.json').write_text(json.dumps(dict(
        source_run=PROFILE['run']['id'], gds_sha256=PROFILE['files'][PROFILE['gds']],
        classification=audit), indent=2)+'\n')
    return audit


if __name__ == '__main__':
    print(json.dumps(package(Path('artifacts'), json.loads(
        Path('/tmp/precheck-source-run.json').read_text()), Path('submission-package')), indent=2))

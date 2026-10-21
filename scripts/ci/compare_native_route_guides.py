"""Compare source-bound trace guides; geometric evidence only, never signoff."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from native_lane_mask_stage_probe import PROFILE
from native_no_final_grt_control import SOURCE_ODB_HASH


def bounds(text, net):
    blocks = re.findall(r'^'+re.escape(net)+r'\s*\n\(\n(.*?)\n\)', text, re.M | re.S)
    if len(blocks) != 1:
        raise ValueError('Missing unique guide net: '+net)
    boxes = []
    for line in blocks[0].splitlines():
        fields = line.split()
        if len(fields) != 5 or not all(re.fullmatch(r'-?\d+', n) for n in fields[:4]):
            raise ValueError('Malformed guide rectangle')
        x1, y1, x2, y2 = map(int, fields[:4])
        if x1 >= x2 or y1 >= y2:
            raise ValueError('Invalid guide rectangle extent')
        boxes.append((x1, y1, x2, y2))
    if not boxes:
        raise ValueError('Empty guide net')
    return dict(rectangles=len(boxes), bbox_dbu=[min(b[0] for b in boxes),
                min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)])


def compare(receipt, initial, final):
    if (receipt.get('source_run') != PROFILE['source_run']
            or receipt.get('source_sha') != PROFILE['source_sha']
            or receipt.get('source_odb_sha256') != SOURCE_ODB_HASH
            or receipt.get('diagnostic_only') is not True
            or receipt.get('qualified') is not False
            or receipt.get('native_final_reroute') is not True):
        raise ValueError('Wrong route trace provenance')
    result = dict(diagnostic_only=True, qualified=False, route_authorized=False, stages={})
    for stage, data in (('initial_route', initial), ('final_route', final)):
        expected = receipt['snapshots'][stage]['after_grt.guide']['sha256']
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('Wrong trace guide bytes: '+stage)
        result['stages'][stage] = {n: bounds(data.decode(), n) for n in PROFILE['nets']}
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--receipt', type=Path, required=True)
    p.add_argument('--initial', type=Path, required=True)
    p.add_argument('--final', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = compare(json.loads(a.receipt.read_text()), a.initial.read_bytes(), a.final.read_bytes())
    a.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))

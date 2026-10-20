"""Strict generated-fabric configuration/mux census, not physical area."""
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import re


def config_bits(text):
    values = re.findall(r'parameter\s+NoConfigBits\s*=\s*(\d+)\b', text)
    if len(values) > 1:
        raise ValueError('Ambiguous configuration parameter')
    return int(values[0]) if values else 0


def switch_cost(text):
    count = config_bits(text)
    pattern = r'//switch matrix multiplexer\s+(\w+)\s+MUX-(\d+)'
    headers = list(re.finditer(pattern, text))
    used = set()
    histogram = Counter()
    outputs = set()
    padded = 0
    for index, header in enumerate(headers):
        name, raw = header.groups()
        n = int(raw)
        if name in outputs or n < 1:
            raise ValueError('Duplicate output or empty mux')
        outputs.add(name)
        block = text[header.end():headers[index+1].start() if index+1 < len(headers) else len(text)]
        selects = [int(a) + int(b or 0) for a, b in re.findall(
            r'ConfigBits\[\s*(\d+)\s*(?:\+\s*(\d+)\s*)?\]', block)]
        width = (n - 1).bit_length()
        if len(selects) != width or used.intersection(selects) or len(set(selects)) != width:
            raise ValueError('Select census differs or overlapping configuration')
        used.update(selects)
        if n == 1:
            if re.search(r'\bcus_mux', block):
                raise ValueError('Direct switch unexpectedly instantiates mux')
            if not re.search(r'assign\s+' + re.escape(name) + r'\s*=\s*\w+\s*;', block):
                raise ValueError('Unsupported direct switch')
        else:
            match = re.search(r'assign\s+' + re.escape(name) + r'_input\s*=\s*\{([^{}]+)\}\s*;', block)
            if not match or len(match[1].split(',')) != n:
                raise ValueError('Declared fan-in differs from input vector')
            mux = re.findall(r'\bcus_mux(\d+)1\s+\w+\s*\(', block)
            if mux != [str(1 << width)]:
                raise ValueError('Unsupported/padding-inconsistent mux implementation')
            slots = [(int(i), re.sub(r'\s+', '', value)) for i, value in re.findall(r'\.A(\d+)\(\s*([^()]*)\)', block)]
            expected = [(i, f'{name}_input[{i}]' if i < n else 'GND0') for i in range(1 << width)]
            if sorted(slots) != expected:
                raise ValueError('Mux data slots differ from declared choices/padding')
            padded += 1 << width
        histogram[str(n)] += 1
    if len(re.findall(r'\bcus_mux\d+1\s+\w+\s*\(', text)) != sum(v for k,v in histogram.items() if k != '1'):
        raise ValueError('Unannotated custom mux')
    if used != set(range(count)):
        raise ValueError('Configuration bits missing, unused or out of range')
    return dict(config_bits=count, outputs=len(outputs), direct_outputs=histogram.get('1', 0),
                programmable_outputs=sum(v for k, v in histogram.items() if k != '1'),
                fanin_histogram=dict(sorted(histogram.items(), key=lambda kv: int(kv[0]))),
                source_choices=sum(int(k)*v for k, v in histogram.items()),
                padded_programmable_input_slots=padded)


def tile_cost(tile, storage, switch):
    total = config_bits(tile)
    if storage is None:
        if total:
            raise ValueError('Missing nonzero configuration storage')
    else:
        if config_bits(storage) != total:
            raise ValueError('Tile/storage parameter mismatch')
        blocks = re.findall(r'\bconfig_latch\s+\w+\s*\((.*?)\);', storage, re.S)
        outputs = []
        for block in blocks:
            bit = re.findall(r'\.Q\(ConfigBits\[(\d+)\]\)', block)
            if len(bit) != 1:
                raise ValueError('Unsupported storage latch')
            outputs.append(int(bit[0]))
        if len(outputs) != total or set(outputs) != set(range(total)):
            raise ValueError('Storage latch census differs')
    matrix = switch_cost(switch)
    if matrix['config_bits'] > total:
        raise ValueError('Switch storage exceeds total')
    return dict(stored_bits=total, switch_bits=matrix['config_bits'],
                nonswitch_bits=total-matrix['config_bits'], switch=matrix)


def fabric_tiles(text):
    rows = list(csv.reader(io.StringIO(text)))
    starts = [i for i,r in enumerate(rows) if r and r[0] == 'FabricBegin']
    ends = [i for i,r in enumerate(rows) if r and r[0] == 'FabricEnd']
    if len(starts) != 1 or len(ends) != 1 or ends[0] <= starts[0]+1:
        raise ValueError('Missing/ambiguous fabric grid')
    grid = rows[starts[0]+1:ends[0]]
    width = len(grid[0])
    if any(len(r) != width or any(not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', x) for x in r) for r in grid):
        raise ValueError('Unsupported or ragged fabric grid')
    return Counter(tile for row in grid for tile in row)


def census(fabric, rtl_dir):
    fabric = Path(fabric)
    rtl_dir = Path(rtl_dir)
    inputs = {str(fabric): hashlib.sha256(fabric.read_bytes()).hexdigest()}
    counts = fabric_tiles(fabric.read_text())
    result = {}
    for tile, copies in sorted(counts.items()):
        paths = [rtl_dir/(tile+'.v'), rtl_dir/(tile+'_switch_matrix.v')]
        storage = rtl_dir/(tile+'_ConfigMem.v')
        if storage.exists():
            paths.append(storage)
        for p in paths:
            inputs[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
        result[tile] = dict(copies=copies, **tile_cost(paths[0].read_text(),
            storage.read_text() if storage.exists() else None, paths[1].read_text()))
    totals = {key: sum(t['copies']*t[key] for t in result.values())
              for key in ('stored_bits', 'switch_bits', 'nonswitch_bits')}
    return dict(tiles=result, totals=totals, input_sha256=inputs,
                physical_area_measured=False, physical_acceptance=False,
                scope='Generated storage latch and declared/checked custom-mux census; includes border tiles, excludes shell and physical mapping. Counts do not predict area or routability.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fabric', type=Path, required=True)
    parser.add_argument('--rtl', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = census(args.fabric, args.rtl)
    with args.out.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write('\n')


if __name__ == '__main__':
    main()

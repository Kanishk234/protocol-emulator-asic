"""Compare observed native latch values with the image's physical frame bits."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from compile.bitfile import BitFile


def audit(modules, snapshot, words, rows=5, cols=8, frames=20, frame_bits=32):
    if len(words) != 2 + cols * frames * (rows + 1):
        raise ValueError('Wrong frame-image length')
    tiles = snapshot['tiles']
    if len(tiles) != rows * cols:
        raise ValueError('Incomplete observed grid')
    result = {}; total = 0; seen = set()
    for tile, observed in tiles.items():
        match = re.fullmatch(r'Tile_X(\d+)Y(\d+)_(\w+)', tile)
        if not match:
            raise ValueError('Unknown observed tile name')
        x, y = map(int, match.group(1, 2)); kind = match[3]
        if not (0 <= x < cols and 0 <= y < rows) or (x, y) in seen:
            raise ValueError('Duplicate or out-of-grid tile')
        seen.add((x, y))
        if kind != observed['tile_type']:
            raise ValueError('Observed tile type changed')
        module = modules[kind]
        cells = {n: c for n, c in module['cells'].items() if c['type'] == 'sg13cmos5l_dlhq_1'}
        if set(cells) != set(observed['q']):
            raise ValueError('Native configuration census differs from observation')
        if not cells:
            result[tile] = 0
            continue
        data = module['ports']['FrameData']; strobe = module['ports']['FrameStrobe']
        if (data['direction'] != 'input' or strobe['direction'] != 'input'
                or len(data['bits']) != frame_bits or len(strobe['bits']) != frames
                or len(set(data['bits'])) != frame_bits or len(set(strobe['bits'])) != frames):
            raise ValueError('Wrong native frame interface')
        used = set()
        for name, cell in cells.items():
            pins = cell['connections']
            if any(len(pins.get(p, [])) != 1 for p in ('D', 'GATE', 'Q')):
                raise ValueError('Non-scalar configuration cell')
            try:
                offset = data['bits'].index(pins['D'][0])
                frame = strobe['bits'].index(pins['GATE'][0])
            except ValueError as error:
                raise ValueError('Configuration cell is not directly frame-connected') from error
            if (frame, offset) in used:
                raise ValueError('Aliased native frame storage')
            used.add((frame, offset))
            # One stream header; each column/frame has its header then rows top-down.
            word = 1 + (x * frames + frame) * (rows + 1) + 1 + (rows - 1 - y)
            value = observed['q'][name]
            expected = str((words[word] >> offset) & 1)
            if value not in ('0', '1') or value != expected:
                raise ValueError(f'Observed configuration mismatch: {tile}/{name}, frame {frame}, bit {offset}')
        total += len(cells); result[tile] = len(cells)
    return dict(passed=True, tiles=len(tiles), compared_configuration_bits=total,
                per_tile=result, scope='Native frame-to-latch image agreement only; no functional or timing qualification.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('native', 'snapshot', 'image', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    image = BitFile.load(args.image)
    if image.arch_version != 0xFE:
        raise ValueError('Diagnostic R1 image required')
    result = audit(json.loads(args.native.read_text())['modules'],
                   json.loads(args.snapshot.read_text()), image.words)
    if result['compared_configuration_bits'] != 8736:
        raise ValueError('Original complete R1 census required')
    result['input_sha256'] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in (args.native, args.snapshot, args.image)}
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))

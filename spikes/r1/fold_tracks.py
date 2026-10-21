"""Owned global-channel transformation, applied only to disposable tile copies."""
import csv
import io
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools'))
from profiling.track_screen import GLOBAL, screen


def fold_csv(text, tracks):
    # Validate width before touching any rows.
    screen({'local': ['source']}, tracks)
    rows = list(csv.reader(io.StringIO(text)))
    for row in rows:
        if len(row) < 6 or row[0] not in ('NORTH', 'EAST', 'SOUTH', 'WEST'):
            continue
        if any(GLOBAL.fullmatch(name+'0') for name in (row[1], row[4])):
            if row[5] != '8':
                raise ValueError('Expected eight original directional tracks')
            row[5] = str(tracks)
    out = io.StringIO()
    csv.writer(out, lineterminator='\n').writerows(rows)
    return out.getvalue()


def transform(library, tiles, tracks):
    """Replace matrices from canonical connections, then narrow wire declarations."""
    library = Path(library)
    proposals = {}
    for tile in tiles:
        if not tile.switch_matrix.connections:
            # Empty corner has no data channels or switch choices to fold.
            continue
        proposal = screen(tile.switch_matrix.connections, tracks)
        if not proposal['custom_mux_arity_supported']:
            raise ValueError('Unsupported folded mux arity')
        directory = library/'tiles/tiny'/tile.name
        matrix = directory/(tile.name+'_r1_folded.list')
        matrix.write_text(''.join(f'{dst},{src}\n' for dst, sources in
                                 proposal['connections'].items() for src in sources))
        path = directory/(tile.name+'.csv')
        rows = list(csv.reader(io.StringIO(path.read_text())))
        matrices = [r for r in rows if r and r[0] == 'MATRIX']
        if len(matrices) != 1:
            raise ValueError('Expected exactly one matrix per tile')
        matrices[0][1] = './'+matrix.name
        out = io.StringIO()
        csv.writer(out, lineterminator='\n').writerows(rows)
        path.write_text(out.getvalue())
        proposals[tile.name] = {k:v for k,v in proposal.items() if k != 'connections'}
    for path in sorted((library/'tiles/tiny').rglob('*.csv')):
        path.write_text(fold_csv(path.read_text(), tracks))
    return proposals

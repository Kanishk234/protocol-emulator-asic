from copy import deepcopy
import pytest

from spikes.r1.configuration_audit import audit


def fixture():
    module = dict(ports={'FrameData': {'direction': 'input', 'bits': [10, 11]},
                         'FrameStrobe': {'direction': 'input', 'bits': [20]}},
                  cells={'cfg': {'type': 'sg13cmos5l_dlhq_1',
                                  'connections': {'D': [11], 'GATE': [20], 'Q': [30]}}})
    snapshot = {'tiles': {'Tile_X0Y0_T': {'tile_type': 'T', 'q': {'cfg': '1'}},
                          'Tile_X0Y1_T': {'tile_type': 'T', 'q': {'cfg': '0'}}}}
    # Header, column/frame header, top row, bottom row, stream footer.
    return {'T': module}, snapshot, [0, 0, 0, 2, 0]


@pytest.mark.parametrize('fault', [None, 'bit', 'unknown', 'missing', 'wiring', 'alias', 'grid'])
def test_image_and_native_snapshot_are_independent_cross_checks(fault):
    modules, snapshot, words = fixture()
    if fault == 'bit': words[3] ^= 2
    if fault == 'unknown': snapshot['tiles']['Tile_X0Y0_T']['q']['cfg'] = 'x'
    if fault == 'missing': snapshot['tiles']['Tile_X0Y0_T']['q'] = {}
    if fault == 'wiring': modules['T']['cells']['cfg']['connections']['D'] = [31]
    if fault == 'alias':
        modules['T']['cells']['cfg2'] = deepcopy(modules['T']['cells']['cfg'])
        for row in snapshot['tiles'].values(): row['q']['cfg2'] = row['q']['cfg']
    if fault == 'grid': snapshot['tiles']['Tile_X0Y2_T'] = snapshot['tiles'].pop('Tile_X0Y1_T')
    if fault is None:
        result = audit(modules, snapshot, words, rows=2, cols=1, frames=1, frame_bits=2)
        assert result['compared_configuration_bits'] == 2
    else:
        with pytest.raises(ValueError): audit(modules, snapshot, words, rows=2, cols=1, frames=1, frame_bits=2)

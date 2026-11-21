from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from clock_fixed_repair import project_state


def test_projected_configuration_uses_native_frame_wiring_without_mutating_observation():
    module = dict(ports={'FrameData': {'bits': list(range(40, 72))},
                         'FrameStrobe': {'bits': list(range(100, 120))}},
                  cells={'cfg': {'connections': {'D': [47], 'GATE': [103]}}})
    observed = {'tiles': {'Tile_X1Y2_T': {'tile_type': 'T', 'q': {'cfg': '0'}}}}
    original = deepcopy(observed)
    words = [0] * 962
    # Column 1, frame 3, row 2: stream word 142; native data bit 7.
    words[142] = 1 << 7
    expected = project_state({'T': module}, observed, words)
    assert expected['tiles']['Tile_X1Y2_T']['q']['cfg'] == '1'
    assert observed == original
    words[142] = 0
    words[141] = 1 << 7
    assert project_state({'T': module}, observed, words) == observed
    module['cells']['cfg']['connections']['D'] = [999]
    with pytest.raises(ValueError):
        project_state({'T': module}, observed, words)

from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from spi_tick_pipeline_compile import pin_global_clock
from fixed_relocation import logical_graph


def test_clock_constraint_preserves_source_graph_and_rejects_ambiguous_controls():
    design = {'modules': {'warp_top': {'cells': {'clkbuf': {
        'type': 'GBUF', 'parameters': {}, 'attributes': {'src': 'frozen'},
        'port_directions': {'I': 'input', 'O': 'output'},
        'connections': {'I': [2], 'O': [3]},
    }}}}}
    original = deepcopy(design)
    pinned, clock = pin_global_clock(design)
    assert clock == 'clkbuf' and design == original
    assert logical_graph(pinned['modules']['warp_top']) == logical_graph(design['modules']['warp_top'])
    assert pinned['modules']['warp_top']['cells'][clock]['attributes'] == {
        'src': 'frozen', 'NEXTPNR_BEL': 'X0Y4/D', 'BEL_STRENGTH': format(6, '032b'),
    }
    with pytest.raises(ValueError):
        pin_global_clock(pinned)
    design['modules']['warp_top']['cells']['second'] = deepcopy(design['modules']['warp_top']['cells'][clock])
    with pytest.raises(ValueError):
        pin_global_clock(design)

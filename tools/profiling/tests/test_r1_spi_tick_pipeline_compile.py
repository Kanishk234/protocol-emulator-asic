from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from spi_tick_pipeline_compile import pin_global_clock,placement_seed,prepare
from fixed_relocation import logical_graph


@pytest.mark.parametrize('threshold',[True,'16',0,8,17,None])
def test_control_sharing_change_is_bounded_before_staging(tmp_path,threshold):
    with pytest.raises(ValueError,match='control-sharing threshold'):
        prepare(tmp_path/'capsule',tmp_path/'proofs',tmp_path/'out',candidate_min_ctrl=threshold)
    assert not (tmp_path/'out').exists()


def test_bounded_candidate_seeds_never_change_original_compile_control():
    assert placement_seed({},'candidate')==1
    for seed in (1,2,3):
        assert placement_seed({'candidate_seed':seed},'control')==1
        assert placement_seed({'candidate_seed':seed},'candidate')==seed
    for seed in (0,4,-1,True,'2',None):
        with pytest.raises(ValueError):placement_seed({'candidate_seed':seed},'candidate')
    with pytest.raises(ValueError):placement_seed({},'unknown')


@pytest.mark.parametrize('ungated',[False,True])
def test_compiler_rejects_proof_for_other_timer_enable_variant(tmp_path,ungated):
    import json
    resource=tmp_path/'capsule/model/resource';resource.mkdir(parents=True)
    (resource/'resource-control.json').write_text(json.dumps(dict(radix='radix8_2',generated_sha256={})))
    case=tmp_path/'proofs/case';case.mkdir(parents=True)
    (case/'result.json').write_text(json.dumps(dict(mode=0,half=4,equivalence_passed=True,
        strict_source_tests=4,ungated_timer=not ungated)))
    with pytest.raises(ValueError,match='different timer enable variant'):
        prepare(tmp_path/'capsule',tmp_path/'proofs',tmp_path/'out',ungated_timer=ungated)
    assert not (tmp_path/'out').exists()


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

"""Frozen context routing must retain geometry and fail closed on process errors."""
import json
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from detailed_context import audit
from detailed_leaf import check_inventories


def test_wire_only_leaf_still_requires_actual_wires():
    expected = dict(cells=0, configuration_latches=0, power_terminals=0)
    text = 'PORT\tI\tn\tINPUT\tSIGNAL\nPORT\tO\tn\tOUTPUT\tSIGNAL\nPGTERMS\t0\n'
    result = check_inventories(text+'REQUIRED_NET\tn\t0\n', text+'REQUIRED_NET\tn\t1\n', expected)
    assert result['required_signal_nets_with_wires'] == 1
    with pytest.raises(ValueError, match='lacks a route'):
        check_inventories(text+'REQUIRED_NET\tn\t0\n', text+'REQUIRED_NET\tn\t0\n', expected)


@pytest.mark.parametrize('code', [1, 124, 137])
def test_failed_process_cannot_accept_even_with_success_markers(tmp_path, code):
    (tmp_path/'plan.json').write_text(json.dumps(dict(case='lut0', expected={}, input_sha256={})))
    (tmp_path/'exit-code.txt').write_text(str(code))
    (tmp_path/'route.log').write_text('R1_DRT_VIOLATIONS 0\nR1_DRT_END\n')
    with pytest.raises(ValueError, match='Router'):
        audit(tmp_path)
    result = json.loads((tmp_path/'result.json').read_text())
    assert not result['passed'] and not result['physical_acceptance'] and not result['timing_acceptance']


@pytest.mark.parametrize('field', ['cells', 'configuration_latches', 'power_terminals'])
def test_context_resource_census_cannot_drift(field):
    expected = dict(cells=1, configuration_latches=1, power_terminals=2)
    text = ('CELL\tc0\tsg13cmos5l_dlhq_1\t0\t0\t1\t1\tR0\tPLACED\n'
            'PGTERMS\t2\n')
    expected[field] += 1
    with pytest.raises(ValueError, match='census'):
        check_inventories(text+'REQUIRED_NET\tn\t0\n', text+'REQUIRED_NET\tn\t1\n', expected)

"""Connection isolation must be explicit and preserve routing rejection."""
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'test_internal'))
import cloud_route_isolation as isolate
import cloud_route_trace as trace
from cloud_route_121_grid import observed_trace, PATCH


def test_control_is_exact_grid_observer_without_net_selection():
    assert isolate.isolation_trace(trace.TRACE, None) == observed_trace(trace.TRACE, PATCH.read_text())


@pytest.mark.parametrize('names', [isolate.CASES['pad31'], isolate.CASES['val30'], isolate.CASES['south_pair']])
def test_selection_is_fixed_literal_before_original_route_and_rethrow(names):
    text = isolate.isolation_trace(trace.TRACE, names)
    assert text.startswith('set warp_selected_nets {' + ' '.join(names) + '}\n')
    assert text.count('log_cmd set_nets_to_route $warp_selected_nets') == 1
    assert text.index('set_nets_to_route') < text.index('log_cmd global_route')
    assert 'return -options $warp_route_options $warp_route_error' in text
    assert '-allow_congestion' not in text


def test_arbitrary_reduced_sets_rejected():
    with pytest.raises(ValueError):
        isolate.isolation_trace(trace.TRACE, ['clk'])

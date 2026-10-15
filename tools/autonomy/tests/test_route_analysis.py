import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('route_analysis', Path(__file__).parents[1] / 'route_analysis.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_crossing_with_both_endpoints_outside_and_boundary_touch():
    cross = [0, 5, 'Metal3', 20, 5, 'Metal3']
    boundary = [0, 0, 'Metal3', 20, 0, 'Metal3']
    via = [5, 5, 'Metal2', 5, 5, 'Metal3']
    result = module.summarize([cross, boundary, via], (2, 0, 10, 10))
    assert result['obs_interior_segments'] == [cross]
    assert result['planar_dbu'] == 40
    assert result['via_segment_count'] == 1


@pytest.mark.parametrize('segment', [
    [0, 0, 'Metal1', 1, 1, 'Metal1'],
    [0, 0, 'Metal1', 1, 0, 'Metal2'],
    [0, 0, 'Metal5', 1, 0, 'Metal5'],
    [0.5, 0, 'Metal1', 1, 0, 'Metal1'],
])
def test_malformed_geometry_rejected(segment):
    with pytest.raises(ValueError):
        module.summarize([segment])


def test_residual_graph_switches_preferred_layers_and_keeps_own_usage():
    segments = [[3600,3600,'Metal1',10800,3600,'Metal1'],
                [10800,3600,'Metal1',10800,3600,'Metal2'],
                [10800,3600,'Metal2',10800,10800,'Metal2']]
    cells = {('Metal3',0,0):1, ('Metal4',1,0):1}
    result = module.residual_paths(cells, 2, 2, {'net':segments}, (100000,100000,200000,200000))['net']
    assert result['shell_terminals_reachable'] == [True, True]
    cells['Metal4',1,0] = 0
    result = module.residual_paths(cells, 2, 2, {'net':segments}, (100000,100000,200000,200000))['net']
    assert result['shell_terminals_reachable'] == [True, False]

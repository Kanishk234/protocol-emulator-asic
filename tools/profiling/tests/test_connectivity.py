import copy
import pytest
from profiling.connectivity import analyze


def cell(x, y, direction, bits):
    return dict(attributes={'NEXTPNR_BEL': f'X{x}Y{y}/A'},
                connections={'P': bits}, port_directions={'P': direction})


def document():
    return {'modules': {'top': {'cells': {
        'driver': cell(0, 0, 'output', [3]),
        'a': cell(1, 0, 'input', [3, '0']),
        'b': cell(2, 2, 'input', [3]),
        'local': cell(0, 0, 'input', [3]),
    }}}}


def test_exact_endpoint_census_not_wirelength():
    result = analyze(document())
    assert result['placed_cells'] == 4
    assert result['signal_bits'] == result['multi_tile_bits'] == 1
    row = result['nets'][0]
    assert row['driver_pins'] == 1 and row['sink_pins'] == 3
    assert row['distinct_tiles'] == 3 and row['tile_bbox_span'] == 4
    assert row['cluster_groups'] == {'1x1': 3, '2x1': 2, '1x2': 3, '2x2': 2}
    assert result['aggregate_cluster_groups_minus_one']['2x2'] == 1
    assert not result['physical_acceptance'] and not result['timing_acceptance']


def test_constants_not_signals_and_no_input_mutation():
    doc = document()
    before = copy.deepcopy(doc)
    analyze(doc)
    assert doc == before
    assert analyze({'modules': {'top': {'cells': {}}}})['max_sink_pins'] == 0


@pytest.mark.parametrize('bad', [True, -1, None, 'invalid'])
def test_reject_bad_signal_bits(bad):
    doc = document()
    doc['modules']['top']['cells']['a']['connections']['P'] = [bad]
    with pytest.raises(ValueError):
        analyze(doc)


def test_reject_unplaced_and_missing_direction():
    for key in ('attributes', 'port_directions'):
        doc = document()
        doc['modules']['top']['cells']['a'][key] = {}
        with pytest.raises(ValueError):
            analyze(doc)


def test_one_flattened_module_required():
    for modules in ({}, {'a': {}, 'b': {}}):
        with pytest.raises(ValueError):
            analyze({'modules': modules})

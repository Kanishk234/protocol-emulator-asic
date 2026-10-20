import pytest
from profiling.config_cost import fabric_tiles, switch_cost, tile_cost


def matrix(n):
    width = (n-1).bit_length()
    if n == 1:
        return '//switch matrix multiplexer out MUX-1\nassign out = source;\n'
    entries = ','.join('source'+str(i) for i in range(n))
    slots = ','.join(f'.A{i}(out_input[{i}])' if i<n else f'.A{i}(GND0)' for i in range(1<<width))
    sels = ','.join(f'.S{i}(ConfigBits[0+{i}])' for i in range(width))
    return (f'parameter NoConfigBits={width};\n//switch matrix multiplexer out MUX-{n}\n'
            f'assign out_input = {{{entries}}};\ncus_mux{1<<width}1 instance ({slots},{sels});\n')


@pytest.mark.parametrize('n', [1,2,3,4,5,8,9,16,17])
def test_mux_padding_and_select_bits(n):
    result = switch_cost(matrix(n))
    assert result['config_bits'] == (n-1).bit_length()
    assert result['source_choices'] == n
    assert result['padded_programmable_input_slots'] == (0 if n==1 else 1<<(n-1).bit_length())


@pytest.mark.parametrize('before,after', [
    ('MUX-3','MUX-4'), ('NoConfigBits=2','NoConfigBits=3'),
    ('ConfigBits[0+1]','ConfigBits[0+0]'), ('cus_mux41','cus_mux81'),
    ('source0,source1,source2','source0,source1'),
    ('.A0(out_input[0])','.A0(GND0)'), ('.A3(GND0)','.A3(source3)'),
])
def test_inconsistent_generated_mux_rejected(before, after):
    with pytest.raises(ValueError):
        switch_cost(matrix(3).replace(before,after))


def test_unannotated_custom_mux_rejected():
    with pytest.raises(ValueError):
        switch_cost('cus_mux21 rogue(.A0(a),.A1(b),.S0(0));')


def test_duplicate_output_rejected():
    with pytest.raises(ValueError):
        switch_cost(matrix(1)*2)


def test_storage_and_switch_census_independent():
    tile = 'parameter NoConfigBits=2;'
    storage = tile+'\nconfig_latch a(.Q(ConfigBits[0]));\nconfig_latch b(.Q(ConfigBits[1]));'
    result = tile_cost(tile, storage, matrix(2))
    assert result['stored_bits']==2 and result['switch_bits']==1 and result['nonswitch_bits']==1
    for invalid in (None, storage.replace('ConfigBits[1]','ConfigBits[0]'), storage.replace('NoConfigBits=2','NoConfigBits=3')):
        with pytest.raises(ValueError):
            tile_cost(tile, invalid, matrix(2))


def test_zero_storage_and_no_switches():
    assert tile_cost('module empty;',None,'module empty;')['stored_bits']==0
    with pytest.raises(ValueError):
        tile_cost('module empty;',None,matrix(2))


def test_grid_count_and_unsupported_cells():
    result = fabric_tiles('FabricBegin\nA,B\nB,A\nFabricEnd\n')
    assert result == {'A':2,'B':2}
    for text in ('FabricBegin\nA\nA,B\nFabricEnd', 'FabricBegin\nA,\nFabricEnd', 'A,B', 'FabricEnd\nFabricBegin'):
        with pytest.raises(ValueError):
            fabric_tiles(text)

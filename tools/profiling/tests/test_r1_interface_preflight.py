from copy import deepcopy
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from interface_preflight import footprint,import_counts,check_neighbors


def grid():
    cells={f'Tile_X{x}Y{y}_LUT4x8_ha':dict(type='LUT4x8_ha',connections={}) for y in range(5) for x in range(8)}
    cells['Tile_X1Y1_LUT4x8_ha']['connections']={'east':[7]}
    cells['Tile_X2Y1_LUT4x8_ha']['connections']={'west':[7]}
    inv={'LUT4x8_ha':dict(die=[0,0,154080,185220],pins={
        'east':dict(direction='OUTPUT',boxes=[['Metal3',153680,1000,154080,1400]]),
        'west':dict(direction='INPUT',boxes=[['Metal3',0,1000,400,1400]])})}
    return dict(cells=cells),inv


def test_borders_preserve_row_and_column_dimensions():
    assert footprint('PRIM2T2S',154.08)==(154.08,185.22)
    assert footprint('N_IO',154.08)==(154.08,56.70)
    assert footprint('W_IO4',154.08)==(68.64,185.22)
    assert footprint('NE_term',154.08)==(68.64,56.70)
    with pytest.raises(ValueError):footprint('LUT4x8_ha',160)


def test_actual_connected_bits_require_same_layer_center_and_opposite_edges():
    design,inv=grid();assert check_neighbors(design,inv,154.08)['adjacent_bit_pairs']==1
    for mutate in ('center','layer','edge','direction','die'):
        bad=deepcopy(inv);pin=bad['LUT4x8_ha']['pins']['west']
        if mutate=='center':pin['boxes'][0][2]+=1
        if mutate=='layer':pin['boxes'][0][0]='Metal2'
        if mutate=='edge':pin['boxes'][0][1]=1
        if mutate=='direction':pin['direction']='OUTPUT'
        if mutate=='die':bad['LUT4x8_ha']['die'][2]+=1
        with pytest.raises(ValueError):check_neighbors(design,bad,154.08)


def test_incomplete_grid_and_nonadjacent_direct_wire_are_rejected():
    design,inv=grid();bad=deepcopy(design);bad['cells'].pop('Tile_X0Y0_LUT4x8_ha')
    with pytest.raises(ValueError):check_neighbors(bad,inv,154.08)
    design['cells']['Tile_X3Y1_LUT4x8_ha']['connections']={'west':[7]}
    with pytest.raises(ValueError):check_neighbors(design,inv,154.08)


def test_only_exact_original_cells_and_bounded_literal_drivers_are_accepted():
    original={'sg13cmos5l_dlhq_1':334}
    assert import_counts(original,original)=={}
    assert import_counts({**original,'sg13cmos5l_tiehi':1},original)=={'sg13cmos5l_tiehi':1}
    for bad in ({'sg13cmos5l_dlhq_1':333},{**original,'sg13cmos5l_tiehi':2},{**original,'sg13cmos5l_buf_1':1}):
        with pytest.raises(ValueError):import_counts(bad,original)


def test_port_alias_normalization_preserves_frozen_bit_identity():
    from interface_preflight import direct_port_aliases
    ports={'source':dict(bits=[7],direction='input'),
           'first':dict(bits=[7],direction='output'),
           'second':dict(bits=[7],direction='output')}
    source='  assign first = source;\n  assign second = first;\n'
    text,changed=direct_port_aliases(source,ports)
    assert text=='  assign first = source;\n  assign second = source;\n'
    assert len(changed)==1 and changed[0]['old_source']=='first'
    bad=deepcopy(ports);bad['second']['bits']=[8]
    with pytest.raises(ValueError):direct_port_aliases(source,bad)
    with pytest.raises(ValueError):direct_port_aliases(' assign first = second;\n assign second = first;\n',ports)
    duplicate='  assign second = source;\n'+source
    clean,changes=direct_port_aliases(duplicate,ports)
    assert clean.count('assign second = source;')==1
    assert any(c.get('removed_duplicate') for c in changes)


def test_connected_track_classes_align_different_border_bus_order():
    from interface_preflight import align_pin_orders
    design=dict(cells={
        'a':dict(type='LUT4x8_ha',connections={'a':[7,8]}),
        'b':dict(type='N_IO',connections={'b':[7,8]})})
    group=lambda pins:[dict(pins=pins,sort_mode='bus_major',reverse_result=False,min_distance=None)]
    orders={'LUT4x8_ha':{'N':group([r'a\[\d+\]'])},
            'N_IO':{'S':group([r'b\[1\]',r'b\[0\]'])}}
    names={'LUT4x8_ha':{'a[0]','a[1]'},'N_IO':{'b[0]','b[1]'}}
    report=align_pin_orders(design,orders,names)
    assert report[0]['anchor']==['LUT4x8_ha','N']
    assert orders['N_IO']['S'][0]['pins']==[r'b\[0\]',r'b\[1\]']
    bad=deepcopy(orders);bad['N_IO']['S'][0]['pins']=[r'b\[0\]']
    with pytest.raises((KeyError,ValueError)):align_pin_orders(design,bad,names)


def test_balanced_neighbors_select_each_actual_column_width():
    from layout_budget import balanced_geometry
    from interface_preflight import balanced_specs
    cells={f'Tile_X{x}Y{y}_LUT4x8_ha':dict(type='LUT4x8_ha',connections={}) for x in range(8) for y in range(5)}
    cells['Tile_X1Y1_LUT4x8_ha']['connections']={'east':[7]}
    cells['Tile_X2Y1_LUT4x8_ha']['connections']={'west':[7]}
    design=dict(cells=cells);inventories={}
    for tile,w,h in balanced_specs(design):
        right=round(w*1000)
        inventories[tile,w,h]=dict(die=[0,0,right,round(h*1000)],pins={
            'east':dict(direction='OUTPUT',boxes=[['Metal3',right-400,1000,right,1400]]),
            'west':dict(direction='INPUT',boxes=[['Metal3',0,1000,400,1400]])})
    assert balanced_geometry(1,1)!=(balanced_geometry(2,1))
    assert check_neighbors(design,inventories,balanced=True)['adjacent_bit_pairs']==1
    bad=deepcopy(inventories);bad['LUT4x8_ha',164.64,185.22]['die'][2]=154080
    with pytest.raises(ValueError):check_neighbors(design,bad,balanced=True)

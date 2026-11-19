from pathlib import Path
import json
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from flat_routes import check_import,component,net_record,section,translate_routes


def test_absolute_points_translate_but_rect_deltas_extensions_and_wildcards_stay():
    route='+ ROUTED Metal2 ( 10 20 0 ) ( * 30 ) NEW Metal3 ( 10 30 ) RECT ( -5 -6 7 8 )'
    moved=translate_routes(route,(100,200))
    assert moved=='+ ROUTED Metal2 ( 110 220 0 ) ( * 230 ) NEW Metal3 ( 110 230 ) RECT ( -5 -6 7 8 )'
    assert translate_routes('',(100,200))==''


@pytest.mark.parametrize('route',[
    '+ FIXED Metal2 ( 10 20 )', '+ ROUTED Metal2 ( missing 20 )',
    '+ ROUTED Metal2 ( 1 2 3 4 )', '+ ROUTED Metal2 ( 1 2 ) RECT ( 1 2 3 )'])
def test_unknown_or_malformed_route_geometry_is_rejected(route):
    with pytest.raises(ValueError):translate_routes(route,(100,200))


def test_component_keeps_master_orientation_and_source_while_translating_origin():
    row='_1_ sg13cmos5l_inv_1 + SOURCE DIST + PLACED ( 10 20 ) FS'
    assert component(row,'tile',(100,200))=='tile/_1_ sg13cmos5l_inv_1 + SOURCE DIST + PLACED ( 110 220 ) FS'
    with pytest.raises(ValueError):component('_1_ cell + UNPLACED','tile',(100,200))


def test_net_parser_separates_connectivity_from_route_geometry():
    row='n ( PIN p ) ( _1_ A ) + USE SIGNAL + ROUTED Metal3 ( 10 20 ) ( 30 * )'
    name,conns,kind,body=net_record(row)
    assert name=='n' and conns==[('PIN','p'),('_1_','A')] and kind=='SIGNAL'
    assert body=='+ ROUTED Metal3 ( 10 20 ) ( 30 * )'
    assert net_record('VPWR ( * VDD ) + USE POWER')[1]==[('*','VDD')]
    with pytest.raises(ValueError):net_record('n ( invalid schema tuple ) + USE SIGNAL')


def test_sections_cannot_drop_or_duplicate_def_entries():
    text='NETS 1 ;\n - n ( _1_ A ) + USE SIGNAL ;\nEND NETS\n'
    assert section(text,'NETS')==['n ( _1_ A ) + USE SIGNAL']
    assert section(text,'VIAS',optional=True)==[]
    with pytest.raises(ValueError):section(text.replace('NETS 1','NETS 2'),'NETS')
    with pytest.raises(ValueError):section(text+text,'NETS')


@pytest.mark.parametrize('fault',[None,'missing_wire','unwired','extra_wire','position','connection'])
def test_flat_import_cannot_drop_wires_or_change_cells_or_connections(tmp_path,fault):
    cell=['tile/_1_','sg13cmos5l_buf_1',100,200,110,220,'R0','PLACED']
    expected=dict(cells=[cell],terms=[['tile/_1_','A','n']],ports={'p':'n'})
    (tmp_path/'expected.json').write_text(json.dumps(expected))
    data='CELL\ttile/_1_\tsg13cmos5l_buf_1\t100\t200\t110\t220\tR0\tPLACED\n'
    data+='ITERM\ttile/_1_\tA\tn\nPORT\tp\tn\tINPUT\tSIGNAL\nREQUIRED_NET\tn\t1\n'
    if fault=='missing_wire':data=data.replace('REQUIRED_NET\tn\t1\n','')
    if fault=='unwired':data=data.replace('REQUIRED_NET\tn\t1','REQUIRED_NET\tn\t0')
    if fault=='extra_wire':data+='REQUIRED_NET\tforeign\t1\n'
    if fault=='position':data=data.replace('\t100\t200','\t101\t200')
    if fault=='connection':data=data.replace('ITERM\ttile/_1_\tA\tn','ITERM\ttile/_1_\tA\tother')
    (tmp_path/'imported.txt').write_text(data)
    if fault is None:assert check_import(tmp_path)['required_signal_nets_with_wires']==1
    else:
        with pytest.raises(ValueError):check_import(tmp_path)

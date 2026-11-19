from pathlib import Path
import json
import re
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from flat_routes import check_import,component,net_record,pin_access_routes,section,translate_routes


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


def test_pin_centerlines_join_abutting_source_pins_without_extending_their_metal():
    left=pin_access_routes('Metal3',(0,0,400,400),(0,0))
    right=pin_access_routes('Metal3',(0,0,400,400),(400,0))
    endpoint_sets=[]
    for routes,bounds in [(left,(0,0,400,400)),(right,(400,0,800,400))]:
        endpoints=set()
        for route in routes[1:]:
            m=re.fullmatch(r'\+ ROUTED Metal3 \( (\d+) (\d+) 0 \) \( (\d+) (\d+) 0 \)',route)
            assert m
            x0,y0,x1,y1=map(int,m.groups());endpoints.update([(x0,y0),(x1,y1)])
            if y0==y1:metal=(x0,y0-100,x1,y1+100)
            else:
                assert x0==x1
                metal=(x0-100,y0,x1+100,y1)
            assert bounds[0]<=metal[0]<metal[2]<=bounds[2]
            assert bounds[1]<=metal[1]<metal[3]<=bounds[3]
        endpoint_sets.append(endpoints)
    assert endpoint_sets[0]&endpoint_sets[1]=={(400,200)}
    for layer,box in [('Metal1',(0,0,400,400)),('Metal3',(0,0,200,400))]:
        with pytest.raises(ValueError):pin_access_routes(layer,box,(0,0))


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

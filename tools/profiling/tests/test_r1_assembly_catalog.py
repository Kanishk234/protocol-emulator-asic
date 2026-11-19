from copy import deepcopy
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from assembly_catalog import catalog,specifications,GATES


def fixture():
    cells={}
    for x in range(8):
        for y in range(5):
            if y==0:kind='NW_term' if x==0 else 'NE_term' if x==7 else 'N_IO'
            elif y==4:kind='SW_term' if x==0 else 'SE_term' if x==7 else 'S_IO2'
            elif x==0:kind='W_IO4'
            elif x==7:kind='E_IO4'
            elif x in (2,5) and y==2:kind='PRIM2T2S'
            else:kind='LUT4x8_ha'
            cells[f'Tile_X{x}Y{y}_{kind}']=dict(type=kind)
    rows=[dict(case=n,passed=True,physical_gate_metrics=dict.fromkeys(GATES,0),
               gds_sha256='a'*64,odb_sha256='b'*64,nl_sha256='c'*64) for n in specifications()]
    return dict(cells=cells),rows


def test_contexts_have_distinct_masters_and_correct_north_south_coordinates():
    top,rows=fixture();r=catalog(top,rows)
    assert len({v['planned_master'] for v in r['contexts'].values()})==26
    assert r['contexts']['lut0']['width_dbu']==154080
    assert r['contexts']['lut1']['width_dbu']==164640
    places={v['instance']:v['origin_dbu'] for v in r['instances']}
    assert places['Tile_X0Y4_SW_term']==[0,0]
    assert places['Tile_X0Y0_NW_term']==[0,612360]
    assert not r['geometry_written'] and not r['assembly_acceptance'] and not r['timing_acceptance']


@pytest.mark.parametrize('fault',['missing','duplicate','failed','gate','hash','position'])
def test_incomplete_or_changed_evidence_cannot_prepare_assembly(fault):
    top,rows=fixture()
    if fault=='missing':rows.pop()
    if fault=='duplicate':rows.append(deepcopy(rows[0]))
    if fault=='failed':rows[0]['passed']=False
    if fault=='gate':rows[0]['physical_gate_metrics'].pop(GATES[0])
    if fault=='hash':rows[0]['gds_sha256']='unknown'
    if fault=='position':
        top['cells']['Tile_X0Y1_alias']=top['cells'].pop('Tile_X0Y2_W_IO4')
    with pytest.raises(ValueError):catalog(top,rows)

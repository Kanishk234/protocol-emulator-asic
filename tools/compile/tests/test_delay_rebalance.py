"""Measured selection and fail-closed preservation checks for a copied layout."""
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/"test_internal"))
from cloud_delay_rebalance import select, audit_change, OLD, NEW


def test_actual_threshold_requires_complete_measurements():
    queries={f"hold{i}":{"state":"CONSTRAINED","slack_ns":"0.3" if i<251 else "0.2"} for i in range(590)}
    result={"observation_complete":True,"source_run":38167697696,"corners":{
        "nom_fast_1p32V_m40C":{"queries":{"min":queries}}}}
    assert select(result)=={f"hold{i}" for i in range(251)}
    queries['hold0']['slack_ns']='0.299999'
    with pytest.raises(ValueError):select(result)
    queries['hold0']['slack_ns']='0.3';queries['hold400']['state']='NO_CONSTRAINED_PATH'
    with pytest.raises(ValueError):select(result)


def fixture():
    old=''.join(f'INST\tcell{i}\t{OLD if i==0 else "buffer"}\t0 0\tR0\tPLACED\n' for i in range(3606))
    old+='PIN\tcell0/A\tINPUT\tSIGNAL\tnet\n'
    new=old.replace(OLD,NEW)
    geometry='META\t1000\t480\n'+''.join(f'BOX\tcell{i}\tCORE\t0\t0\t{4320 if i==0 else 2400}\t3780\n' for i in range(3606))
    modified=geometry.replace('cell0\tCORE\t0\t0\t4320','cell0\tCORE\t0\t0\t3840')
    return old,new,geometry,modified


def test_only_declared_delay_can_shrink():
    old,new,geometry,modified=fixture()
    r=audit_change(old,new,geometry,modified,{'cell0'})
    assert r['selected_cells']==1
    assert r['core_bbox_area_saved_um2']==pytest.approx(1.8144)


@pytest.mark.parametrize('mutation',['connection','clock_position','orientation','macro_size','wrong_master','growth'])
def test_undeclared_physical_or_connectivity_change_rejected(mutation):
    old,new,geometry,modified=fixture()
    if mutation=='connection':new=new.replace('SIGNAL\tnet','SIGNAL\twrong')
    elif mutation=='clock_position':new=new.replace('cell1\tbuffer\t0 0','cell1\tbuffer\t480 0')
    elif mutation=='orientation':new=new.replace('cell0\t'+NEW+'\t0 0\tR0','cell0\t'+NEW+'\t0 0\tMY')
    elif mutation=='macro_size':modified=modified.replace('cell1\tCORE\t0\t0\t2400','cell1\tCORE\t0\t0\t2880')
    elif mutation=='wrong_master':new=new.replace(NEW,'other')
    elif mutation=='growth':modified=modified.replace('cell0\tCORE\t0\t0\t3840','cell0\tCORE\t0\t0\t4800')
    with pytest.raises(ValueError):audit_change(old,new,geometry,modified,{'cell0'})


def test_native_editor_loads_liberty_before_master_swap():
    from cloud_delay_rebalance import EDIT
    assert EDIT.index('read_db') < EDIT.index('read_liberty') < EDIT.index('swapMaster')

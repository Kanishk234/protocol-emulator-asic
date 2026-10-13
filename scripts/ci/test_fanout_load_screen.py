from pathlib import Path
import pytest
from fanout_load_plan import BINDING,plan
from combined_physical_plan import clock_diode_partition,connections
from fanout_load_screen import PROFILE


def clock_case():
    cells={'driver':('sg13cmos5l_buf_8',())}
    cells.update({f'l{i}':('sg13cmos5l_dlhq_1',()) for i in range(6)})
    cells.update({f'a{i}':('sg13cmos5l_antennanp',()) for i in range(6)})
    sinks=[(f'l{i}','GATE') for i in range(6)]+[(f'a{i}','A') for i in range(6)]
    return 'net',('driver','X'),sinks,cells,{'clock_driver':'driver','clock_diode_sources':['net']}


def test_clock_leaf_pins_remain_untouched_and_driver_budget_is_eight():
    moved,kept=clock_diode_partition(*clock_case())
    assert kept==6 and moved==[(f'a{i}','A') for i in range(6)]
    assert kept+(len(moved)+3)//4==8


@pytest.mark.parametrize('fault',['source','driver','master','leaf_pin','diode_master','load_count'])
def test_clock_partition_refuses_unreviewed_functional_clock_changes(fault):
    source,driver,sinks,cells,cfg=clock_case()
    if fault=='source':source='other'
    elif fault=='driver':driver=('other','X')
    elif fault=='master':cells['driver']=('sg13cmos5l_inv_8',())
    elif fault=='leaf_pin':sinks[0]=('l0','CLK')
    elif fault=='diode_master':cells['a0']=('sg13cmos5l_buf_1',())
    else:sinks=sinks[:-1]
    with pytest.raises((ValueError,KeyError)):clock_diode_partition(source,driver,sinks,cells,cfg)


def test_escaped_def_instance_spelling_normalizes_only_in_reviewed_mode():
    text='\nNETS 1 ;\n- net ( clk\\[0\\] X ) ( sink A ) ;\nEND NETS'
    assert ('clk\\[0\\]','X') in connections(text)[1]
    assert ('clk[0]','X') in connections(text,True)[1]


def test_exact_source_binding_and_manual_workflow():
    import yaml
    assert BINDING['source_run']==38433037592 and BINDING['electrical_nets']==9
    assert BINDING['hold_count']==2 and not BINDING['setup']
    assert PROFILE['post_antenna_audit'] is not None
    with pytest.raises(ValueError):plan('old','old','old',{},Path('std.lef'),Path('macro.lef'))
    root=Path(__file__).resolve().parents[2];w=yaml.safe_load((root/'.github/workflows/gds-fanout-load-screen.yaml').read_text())
    d=next(s for s in w['jobs']['harden']['steps'] if 'download-artifact@' in s.get('uses',''))
    assert d['with']['run-id']==38433037592 and d['with']['name']=='gds-decode-combined-route-38433037592'

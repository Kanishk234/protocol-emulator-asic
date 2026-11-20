import copy
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
import pytest
from fixed_relocation import constant_sources,logical_graph


def fixture():
    return {'cells':{'a':{'type':'LUT','parameters':{'INIT':'10'},'port_directions':{'I':'input','O':'output','EN':'input'},'connections':{'I':[2],'O':[3],'EN':[]}}}}


def test_restore_ignores_net_numbers_and_empty_port_serialization():
    old=fixture();new=copy.deepcopy(old)
    new['cells']['a']['connections']={'I':[20],'O':[30]}
    new['cells']['a']['port_directions'].pop('EN')
    assert logical_graph(old)==logical_graph(new)


def test_restore_rejects_signal_merge_or_truth_mutation():
    old=fixture();new=copy.deepcopy(old)
    new['cells']['a']['connections']['O']=[2]
    assert logical_graph(old)!=logical_graph(new)
    new=copy.deepcopy(old);new['cells']['a']['parameters']['INIT']='00'
    assert logical_graph(old)!=logical_graph(new)


def test_constant_pseudo_pip_occupancy_is_not_a_free_cell():
    module={'netnames':{'vcc':{'attributes':{'ROUTING':'X1Y1/LC_O;X1Y1/$CONST1/X1Y1/LC_O;1'}}}}
    assert constant_sources(module)=={'X1Y1/C':1}
    module['netnames']['vcc']['attributes']['ROUTING']='X1Y1/LC_O;X1Y1/$CONST1/X1Y1/LC_O'
    with pytest.raises(ValueError):constant_sources(module)

from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from flat_topology import expected_module,render,verify
from flat_reference import normalize_cells


def fixture():
    physical=dict(cells=[['tile/c','buffer']],terms=[['tile/c','A','n1'],['tile/c','X','n2'],
        ['tile/c','VDD','VPWR'],['tile/c','VSS','VGND']],ports=dict(p='n1',q='n2',VPWR='VPWR',VGND='VGND'))
    shapes=dict(p=dict(direction='input',bits=[2]),q=dict(direction='output',bits=[3]))
    exported=dict(cells={'tile/c':dict(type='buffer',connections=dict(A=[20],X=[21]))},
                  ports=dict(p=dict(direction='input',bits=[20]),q=dict(direction='output',bits=[21])))
    return physical,shapes,exported


def test_net_numbers_can_change_but_every_source_connection_must_match():
    assert verify(*fixture())['passed']


def test_analysis_export_declares_both_input_and_output_aliases_without_tying_configuration():
    p,s,e=fixture();text=render(p,s)
    assert 'assign n1 = p;' in text and 'assign q = n2;' in text
    assert 'buffer \\tile/c  (.A(n1), .X(n2));' in text
    assert 'VDD' not in text and "1'b" not in text and 'initial' not in text
    powered=render(p,s,powered=True)
    assert 'inout VPWR;' in powered and '.VDD(VPWR)' in powered and '.VSS(VGND)' in powered


def test_source_prefix_normalization_is_complete_unique_and_connectivity_preserving():
    cell=dict(type='buffer',connections=dict(A=[2],X=[3]))
    r=normalize_cells(dict(cells={'tile._1_':cell},ports={}),['tile'])
    assert r['cells']=={'tile/_1_':cell}
    with pytest.raises(ValueError):normalize_cells(dict(cells={'foreign._1_':cell}),['tile'])


@pytest.mark.parametrize('fault',['swap','missing','master','pin','port','power','extra_port'])
def test_export_cannot_change_signal_topology_or_source_inventory(fault):
    p,s,e=deepcopy(fixture())
    if fault=='swap':e['cells']['tile/c']['connections']=dict(A=[21],X=[20])
    if fault=='missing':e['cells'].clear()
    if fault=='master':e['cells']['tile/c']['type']='different'
    if fault=='pin':e['cells']['tile/c']['connections'].pop('A')
    if fault=='port':e['ports']['p']['bits']=[21]
    if fault=='power':p['terms'][2][2]='VGND'
    if fault=='extra_port':p['ports']['foreign']='n3'
    with pytest.raises(ValueError):verify(p,s,e)

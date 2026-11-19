from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from assembly_contacts import Union, audit, inventory


def fixture():
    def view(ports):
        return ({p:dict(net=n, kind='SIGNAL', direction='INPUT') for p,n,b in ports},
                {p:[('Metal3',b)] for p,n,b in ports})
    # A wire-only middle leaf aliases distinct graph bits. Both physical
    # boundary contacts are necessary even though the middle contains no cell.
    top = dict(cells={
        'a':dict(type='a',connections={'out':[2]}),
        'b':dict(type='b',connections={'in':[2], 'out':[3]}),
        'c':dict(type='c',connections={'in':[3]})})
    views = dict(
        a=view([('out','out',(90,10,100,20))]),
        b=view([('in','feed',(0,10,10,20)),('out','feed',(90,10,100,20))]),
        c=view([('in','in',(0,10,10,20))]))
    places = [dict(instance=n,context=n,origin_dbu=[i*100,0],size_dbu=[100,100])
              for i,n in enumerate('abc')]
    modules={n:dict(ports={p:dict(bits=[bit]) for p,bit in ports.items()}) for n,ports in
             dict(a=dict(out=2), b={'in':2,'out':2}, c={'in':2}).items()}
    return top,places,views,modules


def test_real_abutment_contacts_and_wire_only_aliases_are_required():
    r=audit(*fixture())
    assert r['passed'] and r['abutting_pin_pairs']==2 and r['logical_signal_nets']==1
    assert not r['geometry_written'] and not r['assembly_acceptance'] and not r['timing_acceptance']


@pytest.mark.parametrize('fault',['gap','layer','corner','open_alias','short'])
def test_missing_contact_wrong_layer_corner_touch_alias_and_short_fail(fault):
    top,places,views,modules=deepcopy(fixture())
    if fault=='gap':places[2]['origin_dbu'][0]+=1
    if fault=='layer':views['c'][1]['in']=[('Metal2',(0,10,10,20))]
    if fault=='corner':views['c'][1]['in']=[('Metal3',(0,20,10,30))]
    if fault=='open_alias':views['b'][0]['out']['net']='separate'
    if fault=='short':top['cells']['c']['connections']['in']=[99]
    r=audit(top,places,views,modules)
    assert not r['passed']
    assert r['short_count']>0 if fault=='short' else r['open_net_count']>0


@pytest.mark.parametrize('fault',['missing_port','constant','outside'])
def test_unmodeled_or_invalid_geometry_is_rejected(fault):
    top,places,views,modules=deepcopy(fixture())
    if fault=='missing_port':top['cells']['a']['connections']={}
    if fault=='constant':top['cells']['a']['connections']['out']=['0']
    if fault=='outside':views['a'][1]['out']=[('Metal3',(90,10,101,20))]
    with pytest.raises(ValueError):audit(top,places,views,modules)


def test_union_has_no_recursion_depth_limit_for_large_native_grid():
    u=Union()
    for i in range(10000):u.join(i+1,i)
    assert u.find(0)==u.find(10000)


def test_inventory_rejects_duplicate_ports_and_missing_or_empty_boxes():
    port='PORT\tp\tn\tINPUT\tSIGNAL\n'
    box='PBOX\tp\tMetal3\t0\t1\t10\t2\n'
    assert inventory(port+box)[0]['p']['net']=='n'
    for bad in [port,port+port+box,port+box.replace('\t10\t2','\t0\t2')]:
        with pytest.raises(ValueError):inventory(bad)

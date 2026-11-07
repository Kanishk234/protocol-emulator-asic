import pytest
from local_route_patch import PITCH, edge, path, patch, audit, pins, component, detour_one, select_detours


def grid():
    free={}
    for x in range(-2,5):
        for y in range(-2,5):
            for z in (2,3,4):
                a=(3600+x*PITCH,3600+y*PITCH,z)
                b=(a[0]+(PITCH if z==3 else 0),a[1]+(0 if z==3 else PITCH),z)
                free[edge(a,b)]=1
    return free


def test_detour_removes_only_actual_overloaded_edge_and_accounts_capacity():
    a=(3600,3600,3);b=(10800,3600,3);e=edge(a,b)
    free=grid();free[e]=-1
    routes={'data':[e],'unrelated':[edge((3600,18000,3),(10800,18000,3))]}
    changed,ledger,left=patch(routes,free,[dict(net='data',edge=e)],[])
    assert e not in changed['data'] and left[e]==0
    assert all(v>=0 for v in left.values()) and len(changed['data'])>1
    audit(routes,{**routes,**changed},ledger)
    assert free[e]==-1 and routes['data']==[e]
    corrupted={**routes,**changed,'unrelated':changed['data']}
    with pytest.raises(ValueError,match='explicit edit'):
        audit(routes,corrupted,ledger)


def test_attachment_reaches_receiver_below_failing_layer_and_keeps_original_tree():
    receiver=(3600,10800,1);up=(3600,10800,2);end=(3600,18000,2)
    original=[edge(receiver,up),edge(up,end)]
    item=dict(net='data',receiver=receiver,diode=(3600,3600,1),maximum_layer=2)
    changed,ledger,left=patch({'data':original},grid(),[],[item])
    assert set(original)<=set(changed['data'])
    assert all(max(a[2],b[2])<=2 for a,b in ledger[0]['added'])
    audit({'data':original},changed,ledger)
    item['diode']=(10800,3600,1)
    with pytest.raises(ValueError,match='bounded path'):
        patch({'data':original},grid(),[],[item])


def test_same_pin_point_needs_no_extra_edge():
    a=(3600,3600,1);b=(3600,3600,2);old=[edge(a,b)]
    new,ledger,_=patch({'n':old},grid(),[],[dict(net='n',receiver=a,diode=a,maximum_layer=2)])
    assert new['n']==old and ledger[0]['added']==[]


def test_higher_layer_connection_does_not_count_as_early_antenna_protection():
    a=(3600,3600,1);b=(3600,10800,1)
    nodes=[a,(3600,3600,2),(3600,3600,3),(3600,3600,4),
           (3600,10800,4),(3600,10800,3),(3600,10800,2),b]
    routes=[edge(x,y) for x,y in zip(nodes,nodes[1:])]
    assert b not in component(routes,a,3)
    assert b in component(routes,a,4)


def test_duplicate_removal_and_forged_ledger_reject():
    e=edge((3600,3600,3),(10800,3600,3))
    with pytest.raises(ValueError,match='one actual'):
        patch({'n':[e,e]},grid(),[dict(net='n',edge=e)],[])
    with pytest.raises(ValueError,match='Unknown'):
        audit({'n':[e]},{'n':[e]},[dict(net='bad',removed=[],added=[])])


def test_no_capacity_and_unresolved_overflow_reject():
    free={k:0 for k in grid()}
    with pytest.raises(ValueError,match='bounded path'):
        path((3600,3600,3),{(10800,3600,3)},free,set())
    free[edge((3600,3600,3),(10800,3600,3))]=-1
    with pytest.raises(ValueError,match='Unresolved'):
        patch({},free,[],[])


@pytest.mark.parametrize('a,b', [((0,0,1),(0,0,2)),((3600,3600,1),(3600,3600,3)),
    ((3600,3600,3),(10800,10800,3)),((3600,3600,3),(18000,3600,3))])
def test_nonatomic_or_offgrid_edges_reject(a,b):
    with pytest.raises(ValueError):edge(a,b)


def test_pin_inventory_parser_rejects_missing_or_duplicate_rows():
    assert pins('n 1\na/A 3600 10800\n')=={'n':{'a/A':(3600,10800)}}
    for text in ('n 2\na/A 3600 10800\n','n 2\na/A 3600 10800\na/A 3600 10800\n','n 0\n'):
        with pytest.raises(ValueError):pins(text)


def test_detour_can_start_on_nearby_existing_tree_component():
    a=(3600,3600,3);b=(10800,3600,3);e=edge(a,b)
    branch=[edge(a,(3600,3600,2)),edge((3600,3600,2),(3600,10800,2)),
            edge((3600,10800,2),(3600,10800,3))]
    free={k:0 for k in grid()};free[e]=-1
    free[edge((3600,10800,3),(10800,10800,3))]=1
    free[edge((10800,3600,2),(10800,10800,2))]=1
    old=branch+[e,edge((10800,3600,2),b)]
    changed,record,left=detour_one(old,free,dict(net='n',edge=e))
    assert set(branch)<=set(changed) and e not in changed and left[e]==0
    audit({'n':old},{'n':changed},[record])


def test_selection_prefers_removing_redundant_crossing_over_new_wire():
    a=(3600,3600,3);b=(10800,3600,3);e=edge(a,b)
    loop=[a,(3600,3600,4),(3600,10800,4),(3600,10800,3),
          (10800,10800,3),(10800,10800,4),(10800,3600,4),b]
    cycle=[e]+[edge(x,y) for x,y in zip(loop,loop[1:])]
    free={k:0 for k in grid()};free[e]=-1
    chosen,_=select_detours({'a':[e],'b':cycle},free,[e],{'a','b'})
    assert chosen[0]['net']=='b'
    changed,ledger,_=patch({'a':[e],'b':cycle},free,chosen,[])
    assert ledger[0]['added']==[]
    audit({'a':[e],'b':cycle},{'a':[e],**changed},ledger)


@pytest.mark.parametrize('kwargs',[{'radius':0},{'radius':65},{'maximum_cost':1601},{'radius':True}])
def test_unbounded_or_invalid_search_limits_reject(kwargs):
    with pytest.raises(ValueError,match='limits'):
        path((3600,3600,3),{(10800,3600,3)},grid(),set(),**kwargs)


def test_wider_search_reaches_real_spare_capacity_without_changing_capacity():
    free={}
    for x in range(-1,3):
        for y in range(8):
            for z in (2,3,4):
                a=(3600+x*PITCH,3600+y*PITCH,z)
                b=(a[0]+(PITCH if z==3 else 0),a[1]+(0 if z==3 else PITCH),z)
                free[edge(a,b)]=0 if z==3 and x==0 and y!=6 else 1
    a=(3600,3600,3);b=(10800,3600,3);e=edge(a,b);free[e]=-1
    before=free.copy()
    with pytest.raises(ValueError,match='bounded path'):
        detour_one([e],free,dict(net='n',edge=e))
    new,record,left=detour_one([e],free,dict(net='n',edge=e,radius=6))
    assert free==before and left[e]==0 and min(left.values())>=0
    assert any(x[1]==3600+6*PITCH and y[1]==x[1] and x[2]==y[2]==3 for x,y in record['added'])
    audit({'n':[e]},{'n':new},[record])

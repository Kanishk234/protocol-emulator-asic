"""Hand-sized native-format fixtures; no WARP workflow authenticity or EDA."""
from collections import Counter

import pytest

from autonomy import corridor_extract as e
from autonomy import native_corridor as raw
from autonomy import native_terminals as terminal
from autonomy import corridor_solver as solver


def fixture(walk=None):
    walk = walk or [(0,0),(1,0),(2,0),(3,0)]
    usage = Counter()
    for a,b in zip(walk,walk[1:]):
        usage[('H' if a[1]==b[1] else 'V',min(a[0],b[0]),min(a[1],b[1]))]+=1
    r=['SCHEMA\twarp-native-corridor-v1','INDEXING\tzero_based_fast_route_layers_and_grid',
       'MODEL_GATE\tusage_ledger_verified\tfalse','VIA_MODEL\tglobal_route_steps_only_no_physical_cut_capacity',
       'GRID\t4\t3\t2\t0\t0\t10']
    for layer in range(2):
        for direction,xmax,ymax in [('H',3,3),('V',4,2)]:
            for y in range(ymax):
                for x in range(xmax):
                    used=usage[direction,x,y] if layer==0 else 0
                    r.append(f'EDGE\t{direction}\t{layer}\t{x}\t{y}\t3\t{used}\t0\t3')
    r+=['NET\t0\t11\tn\t0\t0\t1\t0\t1\t0\t2','DEMAND\t0\t0\t1','DEMAND\t0\t1\t1',
        'PIN\t0\t0\t0\t0\t0','PIN\t0\t1\t3\t0\t0','TREE\t0\t2\t2\t1',
        f'TREE_EDGE\t0\t0\t3\t0\t1\t0\t1\t{len(walk)-1}\t{len(walk)}']
    r += [f'STEP\t0\t0\t{i}\t{a[0]}\t{a[1]}\t0\t{b[0]}\t{b[1]}\t0\t1'
          for i,(a,b) in enumerate(zip(walk,walk[1:]))]
    r += [f'COMPLETE\t1\t1\t{len(walk)-1}']
    t=['SCHEMA\twarp-native-terminals-v1','MODEL_GATE\tterminal_join_verified\tfalse',
       'SCOPE\tcoarse_pin_membership_and_tree_access_not_physical_via_feasibility',
       'INDEXING\tnative_layers_zero_based_database_routing_levels_one_based','DBU\t1000',
       'GLOBAL_GRID\t4\t3\t2\t0\t0\t10','LAYER\t0\t7\t1\tMetal1\tHORIZONTAL',
       'LAYER\t1\t8\t2\tMetal2\tVERTICAL','DATABASE_NET\t11\tn\t0\t0\t0\t1\t0\t0\t2',
       'DATABASE_COMPLETE\t1','GLOBAL_NET\t11\tn\t0\t0\t0\t2\t2\t2\t1\t1\t0',
       'GLOBAL_PIN\t11\t0\tBTERM\t31\t0\t0\tp0\t0\t5\t5\t1\t1\t0\t0\t1\t0\t1',
       'MEMBER\t11\t0\t0\t0',
       'GLOBAL_PIN\t11\t1\tBTERM\t32\t0\t0\tp1\t0\t35\t5\t1\t1\t3\t0\t1\t0\t1',
       'MEMBER\t11\t1\t0\t1','GLOBAL_COMPLETE\t1\t2\t2','NATIVE_GRID\t4\t3\t2\t0\t0\t10',
       'NATIVE_NET\t0\t11\tn\t2\t0\t1\t0\t2\t2\t1\t2','TREE_ACCESS_SUPPORTED\t0\t1',
       'NATIVE_PIN\t0\t0\t0\t0\t0','NATIVE_PIN\t0\t1\t3\t0\t0',
       'NODE\t0\t0\t0\t0\t0\t0\t0\t10000000\t-1','VIA_RANGE\t0\t0\t0\t0\t1',
       'NODE\t0\t1\t3\t0\t1\t0\t0\t10000000\t-1','VIA_RANGE\t0\t1\t0\t0\t1',
       'NODE_PIN\t0\t0\t0','NODE_PIN\t0\t1\t1','NATIVE_COMPLETE\t1\t1\t2\t2','COMPLETE\twarp-native-terminals-v1']
    segments='n\n(\n'+''.join(f'{10*a[0]+5} {10*a[1]+5} Metal1 {10*b[0]+5} {10*b[1]+5} Metal1\n'
                             for a,b in zip(walk,walk[1:]))+')\n'
    return raw.parse_bytes(('\n'.join(r)+'\n').encode()),terminal.parse_bytes(('\n'.join(t)+'\n').encode()),segments


def test_exact_release_keeps_crossings_and_fixed_exterior_private():
    s,t,text=fixture()
    result=e.extract(s,t,text,slots=[0],window=[1,0,2,1])
    g=result['graph'];net=g['nets'][0]
    assert net['boundary_terminals']==['p1_0_0','p2_0_0']
    assert not net['frozen_exterior_components']
    assert result['release']['0']['weighted_demand']==1
    edge=next(v for v in g['edges'] if v['id']=='H_0_1_0')
    assert edge['fixed_usage']==0 and edge['capacity']==3
    solver.validate_witness(g,{'0':['H_0_1_0']})
    assert not result['native_inputs_authenticated'] and not result['physical_acceptance']


def test_outside_detour_is_explicit_equivalence_not_a_shared_resource():
    s,t,text=fixture([(0,0),(1,0),(1,1),(1,2),(2,2),(2,1),(2,0),(3,0)])
    result=e.extract(s,t,text,slots=[0],window=[1,0,2,1]);g=result['graph']
    assert g['nets'][0]['frozen_exterior_components']==[['p1_1_0','p2_1_0']]
    assert len(g['nodes'])==8 and len(g['edges'])==12
    solver.validate_witness(g,{'0':['V_0_1_0','V_0_2_0']})
    assert all(v['direction']!='via' or v['capacity'] is None for v in g['edges'])


def test_old_repeated_traversals_release_multiset_then_new_topology_uses_union():
    s,t,text=fixture([(0,0),(1,0),(2,0),(1,0),(2,0),(3,0)])
    result=e.extract(s,t,text,slots=[0],window=[1,0,2,1])
    assert result['release']['0']['planar_step_occurrences']==3
    assert result['release']['0']['weighted_demand']==3
    assert next(v for v in result['graph']['edges'] if v['id']=='H_0_1_0')['fixed_usage']==0
    solver.validate_witness(result['graph'],{'0':['H_0_1_0']})


@pytest.mark.parametrize('window',[None,[0,0,4,2],[1,0,1,1],[0,0,True,1],[0,0,3]])
def test_invalid_or_outside_window_rejected(window):
    with pytest.raises(e.ExtractionError,match='window|Window'):
        e.extract(*fixture(),slots=[0],window=window)


@pytest.mark.parametrize('old,new',[
    ('5 5 Metal1','6 5 Metal1'),
    ('5 5 Metal1 15 5 Metal1','5 5 Metal1 15 15 Metal1'),
    ('Metal1','UnknownLayer'),
    ('n\n(','other\n('),
])
def test_bad_segment_geometry_or_inventory_rejected(old,new):
    s,t,text=fixture()
    with pytest.raises(e.ExtractionError):e.extract(s,t,text.replace(old,new,1),slots=[0],window=[1,0,2,1])


def test_published_planar_support_must_equal_raw_tree_support():
    s,t,text=fixture()
    # A connected detour still cannot be substituted for the retained native route.
    text='n\n(\n5 5 Metal1 5 15 Metal1\n5 15 Metal1 35 15 Metal1\n35 15 Metal1 35 5 Metal1\n)\n'
    with pytest.raises(e.ExtractionError,match='planar union'):
        e.extract(s,t,text,slots=[0],window=[1,0,2,1])


def test_admission_and_size_gates_precede_graph_construction(monkeypatch):
    s,t,text=fixture()
    monkeypatch.setattr(e.terminals,'audit_selection',lambda *a:{'selected_membership_and_access_verified':False})
    with pytest.raises(e.ExtractionError,match='unsupported'):e.extract(s,t,text,slots=[0],window=[1,0,2,1])
    monkeypatch.setattr(e.terminals,'audit_selection',lambda *a:{'selected_membership_and_access_verified':True})
    monkeypatch.setattr(solver,'MAX_NODES',7)
    with pytest.raises(e.ExtractionError,match='size limits'):e.extract(s,t,text,slots=[0],window=[1,0,2,1])


def test_extractor_never_invokes_solver_and_is_deterministic(monkeypatch):
    monkeypatch.setattr(solver,'solve',lambda *a,**kw:pytest.fail('Extraction must not invoke CP-SAT'))
    assert e.extract(*fixture(),slots=[0],window=[1,0,2,1])==e.extract(*fixture(),slots=[0],window=[1,0,2,1])

from copy import deepcopy
import itertools
import pytest
from autonomy import corridor_reduce as reduction,corridor_solver as model


def graph(edges=None,terminals=None,capacities=None,nets=1):
    points={'a':(0,0),'b':(1,0),'c':(2,0),'d':(3,0),'e':(1,1),'f':(2,1),'g':(4,0)}
    links=edges or [('a','b'),('b','c'),('c','d')]
    used={p for pair in links for p in pair}|set(terminals or ['a','d'])
    return dict(schema_version=1,
        contract=dict(model.CONTRACT,vias='forbidden',nonpreferred='explicit_edges',omitted_constraints=sorted(model.REQUIRED_OMISSIONS)),
        provenance=dict(kind='abstract_fixture',description='independent straight chains, branches and bends',source_sha256=None),
        layers=[dict(id='M',preferred_direction='horizontal')],
        nodes=[dict(id=p,x=points[p][0],y=points[p][1],layer='M') for p in sorted(used)],
        edges=[dict(id=str(i),u=a,v=b,direction='horizontal' if points[a][1]==points[b][1] else 'vertical',capacity=(capacities or [2]*len(links))[i],fixed_usage=0) for i,(a,b) in enumerate(links)],
        nets=[dict(id=str(i),terminals=terminals or ['a','d'],boundary_terminals=[],track_demand_by_layer={'M':1},via_track_demand=None,allowed_planar_layers=['M']) for i in range(nets)])


def oracle(g):
    choices=[]
    for net in g['nets']:
        root=net['terminals'][0];routes=[]
        for bits in itertools.product((0,1),repeat=len(g['edges'])):
            reached={root};changed=True
            while changed:
                before=len(reached)
                for on,e in zip(bits,g['edges']):
                    if on and ({e['u'],e['v']}&reached):reached.update((e['u'],e['v']))
                changed=len(reached)!=before
            if set(net['terminals'])<=reached:routes.append(bits)
        choices.append(routes)
    return any(all(sum(route[i] for route in routes)<=e['capacity'] for i,e in enumerate(g['edges']))
        for routes in itertools.product(*choices))


@pytest.mark.parametrize('caps',itertools.product((0,1,2),repeat=3))
@pytest.mark.parametrize('nets',[1,2])
@pytest.mark.parametrize('topological',[False,True])
def test_reduction_preserves_exhaustive_feasibility_of_straight_chains(caps,nets,topological):
    g=graph(capacities=caps,nets=nets);r=reduction.reduce(g,topological=topological)
    assert oracle(g)==oracle(r['graph'])
    assert len(r['graph']['edges'])==1 and r['graph']['edges'][0]['capacity']==min(caps)


def test_expansion_accounts_exactly_on_every_original_edge_for_shared_routes():
    g=graph(nets=2);r=reduction.reduce(g);edge=r['graph']['edges'][0]['id']
    checked=reduction.expand_and_check(g,r,{'0':[edge],'1':[edge]})
    assert checked['witness']=={'0':['0','1','2'],'1':['0','1','2']}
    assert checked['witness_check']['edge_usage']=={'0':2,'1':2,'2':2}
    assert not checked['physical_acceptance']


def test_terminal_free_branch_pruned_and_terminal_in_chain_retained():
    g=graph(edges=[('a','b'),('b','c'),('c','d'),('b','e'),('d','g')],terminals=['a','c','d'])
    r=reduction.reduce(g)
    assert r['removed_dead_end_edges']==['3','4']
    assert {n['id'] for n in r['graph']['nodes']}=={'a','c','d'}
    assert oracle(g)==oracle(r['graph'])


def test_bends_and_branches_stay_as_anchors():
    g=graph(edges=[('a','b'),('b','e'),('e','f'),('f','c'),('c','d'),('b','c')])
    r=reduction.reduce(g)
    assert {'b','e','f','c'}<={n['id'] for n in r['graph']['nodes']}
    assert oracle(g)==oracle(r['graph'])


def test_isolated_required_terminal_is_not_silently_pruned():
    g=graph(edges=[('a','b')],terminals=['a','d']);r=reduction.reduce(g)
    assert {n['id'] for n in r['graph']['nodes']}=={'a','d'} and not r['graph']['edges']
    assert not oracle(g) and not oracle(r['graph'])


@pytest.mark.parametrize('mutate',[
    lambda g:g['edges'][0].update(fixed_usage=1),
    lambda g:g['nets'][0]['track_demand_by_layer'].update(M=2),
])
def test_reduction_refuses_unsupported_cost_model(mutate):
    g=graph();mutate(g)
    with pytest.raises(ValueError):reduction.reduce(g)


def test_expansion_rejects_tampered_mapping_and_overcapacity_witness():
    g=graph(capacities=[1,1,1],nets=2);r=reduction.reduce(g)
    with pytest.raises(ValueError):reduction.expand_and_check(g,r,{'0':['chain_0'],'1':['chain_0']})
    tampered=deepcopy(r);tampered['paths']['chain_0'].pop()
    with pytest.raises(ValueError,match='reconstructed mapping'):reduction.expand_and_check(g,tampered,{'0':['chain_0'],'1':[]})


def test_reduction_preserves_input_and_is_deterministic():
    g=graph();before=deepcopy(g)
    assert reduction.reduce(g)==reduction.reduce(g)
    assert g==before


@pytest.mark.parametrize('nets',[1,2])
@pytest.mark.parametrize('caps',[(1,1,1,1,1,1),(2,1,1,1,2,1),(2,0,1,1,2,2)])
def test_topological_bend_compression_preserves_parallel_paths_exhaustively(nets,caps):
    g=graph(edges=[('a','b'),('b','e'),('e','f'),('f','c'),('c','d'),('b','c')],capacities=caps,nets=nets)
    r=reduction.reduce(g,topological=True)
    assert len(r['graph']['edges'])==3 and len(r['graph']['nodes'])==4
    assert oracle(g)==oracle(r['graph'])
    assert all(n['y']==0 for n in r['graph']['nodes'])
    assert 'physical_embedding_replaced_by_topological_indices' in r['graph']['contract']['omitted_constraints']


def test_topological_terminal_free_attached_loop_can_be_omitted():
    g=graph(edges=[('a','b'),('b','e'),('e','f'),('f','c'),('c','b')],terminals=['a','b'])
    r=reduction.reduce(g,topological=True)
    assert r['removed_redundant_cycle_edges']==['1','2','3','4']
    assert len(r['graph']['edges'])==1 and oracle(g)==oracle(r['graph'])
    checked=reduction.expand_and_check(g,r,{'0':['chain_0']})
    assert checked['witness']=={'0':['0']}


def test_topological_expansion_checks_original_bend_resources_and_geometry_untouched():
    g=graph(edges=[('a','b'),('b','e'),('e','f'),('f','c'),('c','d')]);before=deepcopy(g)
    r=reduction.reduce(g,topological=True)
    assert len(r['graph']['edges'])==1
    assert reduction.expand_and_check(g,r,{'0':['chain_0']})['witness']=={'0':['0','1','2','3','4']}
    assert g==before


def test_topological_mode_cannot_be_implicitly_enabled_by_text():
    with pytest.raises(ValueError):reduction.reduce(graph(),topological='false')


def test_parallel_chain_capacity_is_allocated_back_to_distinct_original_paths():
    g=graph(edges=[('a','b'),('b','e'),('e','f'),('f','c'),('c','d'),('b','c')],capacities=[2,1,1,1,2,1],nets=2)
    r=reduction.reduce(g,topological=True);all_edges=[e['id'] for e in r['graph']['edges']]
    checked=reduction.expand_and_check(g,r,{'0':all_edges,'1':all_edges})
    usage=checked['witness_check']['edge_usage']
    assert usage['0']==usage['4']==2
    assert usage['1']==usage['2']==usage['3']==usage['5']==1

"""Clock/repair policies must stay identical when changing placement stage."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'test_internal'))
from cloud_prects_reflow import configure,BASE_FLOW,REFLOW,PROTECTED


def test_only_placement_policy_and_flow_change():
    source={k:('original_'+k) for k in PROTECTED}
    source.update(LIB={'slow':['pinned.lib']},MACROS={'fabric':{'gds':['pinned.gds']}},CTS_SINK_CLUSTERING_SIZE=None,meta={'flow':BASE_FLOW})
    control=configure(source,False);reflow=configure(source,True)
    for key in (*PROTECTED,'LIB','MACROS'):
        assert control[key]==reflow[key]==source[key]
    assert control['CTS_SINK_CLUSTERING_SIZE']==reflow['CTS_SINK_CLUSTERING_SIZE']==8
    assert control['meta']['flow']==BASE_FLOW
    assert reflow['meta']['flow']==REFLOW
    assert reflow['meta']['flow'].index('OpenROAD.GlobalPlacement')<reflow['meta']['flow'].index('OpenROAD.CTS')
    assert reflow['meta']['flow'].index('OpenROAD.CTS')<reflow['meta']['flow'].index('OpenROAD.ResizerTimingPostCTS')
    assert reflow['PL_TIMING_DRIVEN'] is False
    assert source['CTS_SINK_CLUSTERING_SIZE'] is None


def test_configure_does_not_share_mutable_flow_lists():
    result=configure({},True)
    result['meta']['flow'].append('unexpected')
    assert 'unexpected' not in REFLOW and 'unexpected' not in configure({},True)['meta']['flow']

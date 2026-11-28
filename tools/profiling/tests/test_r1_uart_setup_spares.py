"""Reject stale or weakened parent evidence before creating a derived image."""
import json
from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from uart_setup_spares import prepare,LOADED,SNAPSHOT


@pytest.mark.parametrize('mutation',['failed','source','setup','hold','coverage','loop','state'])
def test_parent_must_remain_exact_and_qualified(tmp_path,mutation):
    source=tmp_path/'source';p=source/'sa_functional';p.mkdir(parents=True)
    observation=dict(passed=True,image_sha256=LOADED,observed_configuration_sha256=SNAPSHOT,configuration_bits=8736)
    data=dict(run='46175928642',source_sha='6c34b82217aa58938ac9be8bbf4a70108a62620c',passed=True,
              cases={'candidate':observation,'shell':dict(observation)})
    timing=dict(run=data['run'],source_sha=data['source_sha'],model_qualified=True,
                models={k:dict(worst_slack_ns=v,structural_loops=0,loop_policy_sensitive=False)
                        for k,v in [('setup',-23.209684),('hold',-1.56783)]},coverage={'active':{'passed':True}})
    if mutation=='failed':data['passed']=False
    if mutation=='source':data['source_sha']='stale'
    if mutation in ('setup','hold'):timing['models'][mutation]['worst_slack_ns']=0
    if mutation=='coverage':timing['coverage']['active']['passed']=False
    if mutation=='loop':timing['models']['setup']['structural_loops']=1
    if mutation=='state':data['cases']['candidate']['observed_configuration_sha256']='different'
    (p/'result.json').write_text(json.dumps(data));t=source/'r1_loop_timing';t.mkdir()
    (t/'result.json').write_text(json.dumps(timing))
    with pytest.raises(ValueError,match='exact native'):
        prepare(tmp_path/'capsule',tmp_path/'native',tmp_path/'trial',source,tmp_path/'out')
    assert not (tmp_path/'out').exists()

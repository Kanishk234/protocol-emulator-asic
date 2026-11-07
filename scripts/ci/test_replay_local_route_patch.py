import json
import pytest
from replay_local_route_patch import replay
from test_local_route_patch import grid
from local_route_patch import edge


def fixture(tmp_path):
    e=edge((3600,3600,3),(10800,3600,3))
    rows=[[a,b,1,2 if (a,b)==e else 0] for a,b in grid()]
    (tmp_path/'probe_grid.json').write_text(json.dumps(rows))
    data=dict(routes={'n':[e]},detours=[dict(net='n',edge=e)],attachments=[],capacity_input='probe_grid.json')
    (tmp_path/'planning_inputs.json').write_text(json.dumps(data))
    return data,rows


def test_replay_is_offline_and_never_claims_physical_qualification(tmp_path):
    fixture(tmp_path)
    before={p.name:p.read_bytes() for p in tmp_path.iterdir()}
    result=replay(tmp_path)
    assert result['changed_nets']==['n'] and result['minimum_remaining_headroom']==0
    assert result['physical_qualified'] is False and result['timing_measured'] is False
    assert {p.name:p.read_bytes() for p in tmp_path.iterdir()}==before


def test_unknown_capacity_source_and_duplicate_capacity_reject(tmp_path):
    data,rows=fixture(tmp_path)
    data['capacity_input']='../other.json'
    (tmp_path/'planning_inputs.json').write_text(json.dumps(data))
    with pytest.raises(ValueError,match='Unexpected'):replay(tmp_path)
    fixture(tmp_path)
    (tmp_path/'probe_grid.json').write_text(json.dumps(rows+[rows[0]]))
    with pytest.raises(ValueError,match='Duplicate'):replay(tmp_path)

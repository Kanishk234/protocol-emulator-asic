import json
from copy import deepcopy
from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from sa_functional import admit_response_identity


def fixture():
    row=json.loads((Path(__file__).resolve().parents[3]/'spikes/r1/response_lane_compile_sources.json').read_text())['seeds']['1']
    cases={n:dict(response_lane=flag,uart_buffer=flag,local_capture=False,min_ctrl=4,
        response_transform=deepcopy(row['response_transform']) if flag else None,
        buffer_transform=deepcopy(row['buffer_transform']) if flag else None)
        for n,flag in [('control',False),('candidate',True)]}
    return cases,row


def test_exact_response_placement_chain_is_admitted():
    cases,row=fixture();admit_response_identity(cases,row)


@pytest.mark.parametrize('change',['flag','control','buffer','threshold','site','chain','proof','graph'])
def test_mixed_or_changed_response_placement_is_rejected(change):
    cases,row=fixture()
    if change=='flag':cases['candidate']['response_lane']=1
    if change=='control':cases['control']['response_lane']=True
    if change=='buffer':cases['candidate']['uart_buffer']=False
    if change=='threshold':cases['candidate']['min_ctrl']=True
    if change=='site':row['response_transform']['required_bel']='X1Y1/A';cases['candidate']['response_transform']=deepcopy(row['response_transform'])
    if change=='chain':row['input_transform']['original_json_sha256']='stale'
    if change=='proof':cases['candidate']['response_transform']['proof_sha256']='stale'
    if change=='graph':row['response_transform']['logical_graph_preserved']=1;cases['candidate']['response_transform']=deepcopy(row['response_transform'])
    with pytest.raises(ValueError,match='Response-lane'):admit_response_identity(cases,row)

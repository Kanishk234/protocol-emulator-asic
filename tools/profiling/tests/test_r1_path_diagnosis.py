from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from path_diagnosis import partition


def test_unknown_or_input_endpoint_cannot_be_reported_as_output():
    ports={'out':{'direction':'output'},'in':{'direction':'input'}}
    for name in ('in','typo/D','unknown'):
        with pytest.raises(ValueError):partition({name:-1},{'ff':{}},ports)


def test_internal_and_boundary_failures_remain_separate():
    result=partition({'ff/D':-2,'out':-4},{'ff':{}},{'out':{'direction':'output'}})
    assert result['internal_register']['negative_count']==1
    assert result['internal_register']['worst'][0]['endpoint']=='ff/D'
    assert result['macro_output']['worst'][0]['slack_ns']==-4

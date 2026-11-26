from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from upstream_input import isolated_chain


def test_isolation_accepts_only_single_input_chain():
    a,b,c=[('X1Y1',n) for n in ('jump','end','LD_I2')]
    graph={b:[a],c:[b]}
    assert isolated_chain(graph,a,c)==[a,b,c]
    with pytest.raises(ValueError):isolated_chain({**graph,('X1Y1','LE_I0'):[b]},a,c)
    with pytest.raises(ValueError):isolated_chain({**graph,a:[c]},a,c)


def test_isolation_rejects_cycles_and_missing_target():
    a,b,c=[('X1Y1',n) for n in ('jump','end','LD_I2')]
    with pytest.raises(ValueError):isolated_chain({a:[b],b:[a]},a,c)
    with pytest.raises(ValueError):isolated_chain({b:[a]},a,c)

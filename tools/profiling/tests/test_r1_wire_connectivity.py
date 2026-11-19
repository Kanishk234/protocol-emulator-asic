from types import SimpleNamespace
import pytest
from profiling.r1_wire_connectivity import wire_boundary_connected


def terminal(kind='SIGNAL', peers=2, wire=True, grid=False, boxes=False):
    net = SimpleNamespace(getSigType=lambda:kind, getBTerms=lambda:[object()]*peers,
                          getWire=lambda:object() if wire else None,
                          getSWires=lambda:[object()] if grid else [])
    pin = SimpleNamespace(getBoxes=lambda:[object()] if boxes else [])
    return SimpleNamespace(getNet=lambda:net,getBPins=lambda:[pin])


def test_boundary_pair_requires_an_actual_wire():
    assert wire_boundary_connected(terminal())
    assert not wire_boundary_connected(terminal(wire=False))
    assert not wire_boundary_connected(terminal(peers=1))
    assert not wire_boundary_connected(SimpleNamespace(getNet=lambda:None))


@pytest.mark.parametrize('kind',['POWER','GROUND'])
def test_power_requires_both_grid_and_pin_geometry(kind):
    assert wire_boundary_connected(terminal(kind=kind,grid=True,boxes=True))
    assert not wire_boundary_connected(terminal(kind=kind,grid=False,boxes=True))
    assert not wire_boundary_connected(terminal(kind=kind,grid=True,boxes=False))

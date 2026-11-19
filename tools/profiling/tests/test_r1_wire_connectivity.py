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


def test_patch_application_is_exact_and_rejects_source_drift():
    from profiling.r1_wire_connectivity import apply_unified_patch
    patch = ('--- a/disconnected_pins.py\n+++ b/disconnected_pins.py\n'
             '@@ -1,3 +1,3 @@\n one\n-two\n+replacement\n three\n')
    assert apply_unified_patch('one\ntwo\nthree\n', patch) == 'one\nreplacement\nthree\n'
    with pytest.raises(ValueError, match='context'):
        apply_unified_patch('one\nchanged\nthree\n', patch)
    with pytest.raises(ValueError, match='counts'):
        apply_unified_patch('one\ntwo\nthree\n', patch.replace('-1,3','-1,4'))

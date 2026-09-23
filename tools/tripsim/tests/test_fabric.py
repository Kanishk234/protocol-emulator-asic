"""Channel fabric rules (ARCHITECTURE.md §4, §14 rules F1-F4)."""

import pytest

from tripsim.fabric import Fabric


def setup(modes):
    f = Fabric()
    p = f.producer("P")
    ports = []
    for i, mode in enumerate(modes):
        f.port(f"C{i}")
        f.connect(f"C{i}", "P", mode)
        ports.append(f.ports[f"C{i}"])
    return f, p, ports


def test_blocking_multicast_releases_after_all_take():
    f, p, (a, b) = setup(["blocking", "blocking"])
    p.load(0, 1); f.commit()
    assert a.avail() and b.avail() and not p.free()
    a.take(); f.commit()
    assert not a.avail() and b.avail() and not p.free()
    b.take(); f.commit()
    assert p.free()
    p.load(0, 2); f.commit()
    assert a.head() == (0, 2) and b.head() == (0, 2)


def test_same_clock_take_does_not_free_producer():
    f, p, (a,) = setup(["blocking"])
    p.load(0, 1); f.commit()
    a.take()
    with pytest.raises(RuntimeError):
        p.load(0, 2)          # registered release: free only from the next clock


def test_tap_never_blocks_and_counts_drops():
    f, p, (tap,) = setup(["tap"])
    for v in range(5):
        assert p.free()
        p.load(0, v); f.commit()
    assert tap.dropped == 4 and tap.head() == (0, 4)
    tap.take(); p.load(0, 9); f.commit()      # take and overwrite in one clock: no drop
    assert tap.dropped == 4 and tap.head() == (0, 9)


def test_enable_does_not_expose_stale_token():
    f, p, _ = setup([])
    p.load(0, 7); f.commit()
    f.port("late"); f.connect("late", "P")
    assert not f.ports["late"].avail()

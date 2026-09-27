from hypothesis import given, strategies as st

from refmodels.prims import Shift, Timer


def run_timer(t, cycles, en=1):
    tcs = []
    for _ in range(cycles):
        tcs.append(t.outputs(en=en)["tc"])
        t.clock(en=en)
    return tcs


@given(st.integers(0, 300))
def test_free_running_period_is_reload_plus_one(reload):
    t = Timer(reload)
    t.clock(rst=1)
    tcs = run_timer(t, 3 * (reload + 1))
    hits = [i for i, v in enumerate(tcs) if v]
    assert hits == [reload, 2 * reload + 1, 3 * reload + 2]


@given(st.integers(1, 300))
def test_half_load_fires_after_half_period(reload):
    t = Timer(reload)
    t.clock(load=1, half=1)
    tcs = run_timer(t, reload + 1)
    assert tcs.index(1) == reload >> 1


@given(st.integers(0, 100))
def test_oneshot_fires_once_until_reloaded(reload):
    t = Timer(reload, oneshot=True)
    t.clock(rst=1)
    assert sum(run_timer(t, 3 * (reload + 1) + 5)) == 1
    t.clock(load=1)
    assert sum(run_timer(t, 2 * (reload + 1))) == 1


def test_en_low_holds_and_masks_tc():
    t = Timer(3)
    t.clock(rst=1)
    run_timer(t, 3)                      # count 0 now
    assert t.outputs(en=0)["tc"] == 0
    run_timer(t, 5, en=0)
    assert t.outputs(en=1)["tc"] == 1


@given(st.integers(0, 255), st.booleans())
def test_shift_out_a_byte(byte, msb_first):
    s = Shift(8, msb_first)
    s.clock(load=1, d=byte)
    bits = []
    for _ in range(8):
        assert not s.outputs()["done"]
        bits.append(s.outputs()["sout"])
        s.clock(step=1)
    assert s.outputs()["done"]
    order = range(7, -1, -1) if msb_first else range(8)
    assert bits == [(byte >> i) & 1 for i in order]


@given(st.integers(0, 255), st.booleans())
def test_shift_in_a_byte(byte, msb_first):
    s = Shift(8, msb_first)
    s.clock(rst=1)
    order = range(7, -1, -1) if msb_first else range(8)
    for i in order:
        s.clock(step=1, sin=(byte >> i) & 1)
    assert s.outputs()["q"] == byte and s.outputs()["done"]


@given(st.integers(1, 15), st.integers(0, 40))
def test_done_after_len_steps_and_stays(length, extra):
    s = Shift(length)
    s.clock(load=1, d=0)
    for i in range(length + extra):
        assert s.outputs()["done"] == int(i >= length)
        s.clock(step=1)
    assert s.outputs()["done"]


def test_priority_rst_over_load_over_step():
    s = Shift(4)
    s.clock(load=1, d=0xA5)
    s.clock(rst=1, load=1, d=0xFF, step=1)
    assert s.outputs()["q"] == 0
    s.clock(load=1, d=0x3C, step=1, sin=1)
    assert s.outputs()["q"] == 0x3C

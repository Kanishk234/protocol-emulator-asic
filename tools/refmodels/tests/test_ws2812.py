"""The WS2812 reference decoder against its own ideal encoder and the datasheet's limits."""

from hypothesis import given, settings, strategies as st

from refmodels import ws2812


@given(st.lists(st.integers(0, 255), min_size=1, max_size=12), st.sampled_from([10, 20, 100 / 3]))
@settings(max_examples=60, deadline=None)
def test_roundtrip(data, clk_ns):
    frames, errors = ws2812.decode(ws2812.encode(data, clk_ns), clk_ns)
    assert errors == []
    assert frames == [data]


def test_two_frames_split_by_reset():
    clk = 20
    w = ws2812.encode([1, 2, 3], clk) + ws2812.encode([0xFF], clk, lead_ns=0)
    assert ws2812.decode(w, clk) == ([[1, 2, 3], [0xFF]], [])


def test_short_gap_is_not_a_reset():
    clk = 20
    a = ws2812.encode([0xA5], clk, reset_ns=0)
    b = ws2812.encode([0x5A], clk, lead_ns=0)
    frames, errors = ws2812.decode(a + [0] * 50 + b, clk)   # 1 us extra low: a long bit period
    assert frames == [[0xA5, 0x5A]]
    assert errors and "bit period" in errors[0][1]


def test_bad_high_time_is_reported():
    clk = 20
    w = ws2812.encode([0x00], clk, t0h=600)                   # 0.6 us: between the windows
    frames, errors = ws2812.decode(w, clk)
    assert errors and "neither" in errors[0][1]


def test_partial_byte_is_reported():
    clk = 20
    w = ws2812.encode([0xFF], clk)
    w = w[:len(w) // 2] + [0] * 3000
    frames, errors = ws2812.decode(w, clk)
    assert any("whole bytes" in e[1] for e in errors)

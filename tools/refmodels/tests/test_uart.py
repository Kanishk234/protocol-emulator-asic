from hypothesis import given, strategies as st

from refmodels.uart import Frame, decode, encode, frame_bits


def test_frame_bits_8n1():
    # 0x55 = 0101_0101, LSB first
    assert frame_bits(0x55) == [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]


def test_frame_bits_parity_and_two_stops():
    assert frame_bits(0x03, parity="even", stop=2)[-3:] == [0, 1, 1]
    assert frame_bits(0x03, parity="odd")[-2:] == [1, 1]


@given(st.lists(st.integers(0, 255), min_size=1, max_size=6),
       st.integers(1, 17), st.integers(0, 9), st.integers(0, 5))
def test_roundtrip(data, cpb, gap, idle):
    wave = encode(data, cpb, gap=gap, idle_before=idle) + [1] * cpb
    assert decode(wave, cpb) == [Frame(d, True) for d in data]


@given(st.integers(0, 255), st.sampled_from(["even", "odd"]))
def test_roundtrip_parity(byte, parity):
    wave = encode([byte], 8, parity=parity) + [1] * 8
    assert decode(wave, 8, parity=parity) == [Frame(byte, True, True)]


def test_framing_error_when_stop_bit_low():
    wave = encode([0xA5], 8)
    wave[-8:] = [0] * 8  # stop bit forced low
    wave += [1] * 16
    assert decode(wave, 8)[0] == Frame(0xA5, False)


def test_short_glitch_is_not_a_start_bit():
    wave = [1] * 5 + [0] * 2 + [1] * 20
    assert decode(wave, 8) == []

import pytest
from hypothesis import given, strategies as st

from refmodels.spi import Target, decode, idle_ok


def controller_wave(data, cpol, cpha, half=3, gap=4):
    """A textbook SPI controller written directly from the mode definitions (for model tests only):
    returns per-clock cs_n, sck, mosi for one transaction."""
    cs, sck, mosi = [1] * gap, [cpol] * gap, [1] * gap
    level = cpol
    for byte in data:
        bits = [(byte >> (7 - k)) & 1 for k in range(8)]
        for k, b in enumerate(bits):
            if cpha == 0:
                cs += [0] * half; sck += [level] * half; mosi += [b] * half      # data before leading edge
                level ^= 1
                cs += [0] * half; sck += [level] * half; mosi += [b] * half      # leading edge: sample
                level ^= 1                                                       # trailing edge next
            else:
                level ^= 1
                cs += [0] * half; sck += [level] * half; mosi += [b] * half      # leading: change
                level ^= 1
                cs += [0] * half; sck += [level] * half; mosi += [b] * half      # trailing: sample
    cs += [0] * half + [1] * gap
    sck += [cpol] * (half + gap)
    mosi += [1] * (half + gap)
    return cs, sck, mosi


@pytest.mark.parametrize("cpol", [0, 1])
@pytest.mark.parametrize("cpha", [0, 1])
def test_decode_textbook_controller(cpol, cpha):
    data = [0xA5, 0x3C, 0x00, 0xFF]
    cs, sck, mosi = controller_wave(data, cpol, cpha)
    assert idle_ok(cs, sck, cpol)
    got = decode(cs, sck, mosi, [0] * len(cs), cpol, cpha)
    assert [m for m, _ in got[0]] == data


@given(st.lists(st.integers(0, 255), min_size=1, max_size=5),
       st.lists(st.integers(0, 255), min_size=1, max_size=5),
       st.integers(0, 1), st.integers(0, 1), st.integers(1, 4))
def test_target_roundtrip(data, resp, cpol, cpha, half):
    cs, sck, mosi = controller_wave(data, cpol, cpha, half=half)
    tgt = Target(cpol, cpha, responses=resp)
    miso = [tgt.step(c, s, o) for c, s, o in zip(cs, sck, mosi)]
    assert tgt.transactions == [data]
    got = decode(cs, sck, mosi, miso, cpol, cpha)
    expected_miso = [resp[i % len(resp)] for i in range(len(data))]
    assert got == [list(zip(data, expected_miso))]


@pytest.mark.parametrize("cpha", [0, 1])
def test_responses_continue_across_transactions(cpha):
    """The target's response stream is not skipped or repeated across CS transactions."""
    tgt = Target(0, cpha, responses=[0x11, 0x22, 0x33])
    got = []
    for data in ([0xAA, 0xBB], [0xCC], [0xDD, 0xEE]):
        cs, sck, mosi = controller_wave(data, 0, cpha)
        miso = [tgt.step(c, s, o) for c, s, o in zip(cs, sck, mosi)]
        got += [x for t in decode(cs, sck, mosi, miso, 0, cpha) for _, x in t]
    assert got == [0x11, 0x22, 0x33, 0x11, 0x22]

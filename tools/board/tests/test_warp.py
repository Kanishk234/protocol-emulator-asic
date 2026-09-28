"""The demo-board loader (tools/board/warp.py) builds exactly the transactions of the reference
host module (tools/host/protocol.py) and reads .wbit files exactly as tools/compile/bitfile.py
writes them. Its chip-level behaviour is tested in test/test_bitstream.py::test_board_loader."""

import random
import zlib
from pathlib import Path

import pytest
from hypothesis import given, settings, strategies as st

from board import warp
from compile.bitfile import BitFile
from host import protocol

BITS = Path(__file__).resolve().parents[3] / "test" / "bitstreams"


@given(st.binary(max_size=300))
@settings(max_examples=100, deadline=None)
def test_crc32_fallback_matches_zlib(data):
    saved = warp._crc32
    try:
        warp._crc32 = None                       # the pure-Python path MicroPython may need
        assert warp.crc32(data) == zlib.crc32(data) & 0xFFFFFFFF
    finally:
        warp._crc32 = saved
    assert warp.crc32(data) == zlib.crc32(data) & 0xFFFFFFFF


@pytest.mark.parametrize("chunk", [1, 5, 64])
def test_load_transactions_match_reference(chunk):
    rng = random.Random(chunk)
    words = [protocol.SYNC_WORD] + [rng.getrandbits(32) for _ in range(130)]
    ref = [[int(b) for b in t] for t in protocol.load_transactions(words, chunk, 0x0003)]
    assert warp.load_transactions(words, 0x0003, chunk) == ref


@pytest.mark.parametrize("path", sorted(BITS.glob("*.wbit")), ids=lambda p: p.stem)
def test_parse_wbit_matches_bitfile(path):
    data = path.read_bytes()
    bf = BitFile.from_bytes(data)
    assert warp.parse_wbit(data) == (bf.arch_version, bf.words)


def test_parse_wbit_rejects_corruption():
    data = bytearray((BITS / "counter4.wbit").read_bytes())
    data[40] ^= 1
    with pytest.raises(warp.WarpError):
        warp.parse_wbit(bytes(data))
    with pytest.raises(warp.WarpError):
        warp.parse_wbit(b"XXXX" + bytes(data[4:]))


@pytest.mark.parametrize("byte", range(256))
def test_status_decode_matches_reference(byte):
    ref = protocol.Status.decode(byte)
    got = warp.decode_status(byte)
    state = ref.state.name if isinstance(ref.state, protocol.State) else ref.state
    assert got == {"state": state, "rx_valid": ref.rx_valid, "tx_ready": ref.tx_ready,
                   "ch_overflow": ref.ch_overflow, "user_attention": ref.user_attention,
                   "error_pending": ref.error_pending}


def test_command_bytes_match_reference():
    assert [warp.READ_ID, 0, 0, 0, 0] == [int(b) for b in protocol.tx_read_id()]
    assert [warp.READ_STATUS, 0, 0] == [int(b) for b in protocol.tx_read_status()]
    assert [warp.CH_WRITE, 1, 0xA5] == [int(b) for b in protocol.tx_ch_write(0xA5, last=True)]
    assert [warp.CH_READ, 0] == [int(b) for b in protocol.tx_ch_read()]
    assert [warp.USER_STATUS, 0] == [int(b) for b in protocol.tx_user_status()]
    for name in ("RUN", "STOP", "USER_RESET"):
        assert getattr(warp, name) == int(protocol.Op[name])

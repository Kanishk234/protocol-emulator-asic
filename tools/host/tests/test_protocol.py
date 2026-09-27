import zlib

import pytest
from hypothesis import given, strategies as st

from host.protocol import (ARCH_VERSION, ArchMismatch, Op, State, Status,
                           checked_load_transactions, crc32_words, load_transactions,
                           parse_read_id, tx_ch_write, tx_load_begin, words_to_bytes)


def test_crc_is_ieee_over_big_endian_bytes():
    assert crc32_words([0x12345678]) == zlib.crc32(bytes([0x12, 0x34, 0x56, 0x78]))
    assert crc32_words([]) == 0


@given(st.integers(0, 255))
def test_status_roundtrip(byte):
    s = Status.decode(byte)
    if isinstance(s.state, State):
        assert s.encode() == byte


def test_status_fields():
    s = Status.decode(0b011_1_1_0_1_0)   # RUNNING, rx_valid, tx_ready, attention
    assert s.state == State.RUNNING and s.rx_valid and s.tx_ready and s.user_attention
    assert not s.ch_overflow and not s.error_pending and s.irq


def test_load_begin_layout():
    assert tx_load_begin(0x0123) == [Op.LOAD_BEGIN, ARCH_VERSION >> 8, ARCH_VERSION & 0xFF, 0x01, 0x23]


@given(st.lists(st.integers(0, 0xFFFFFFFF), min_size=1, max_size=200), st.integers(1, 64))
def test_load_transactions_carry_all_words_and_crc(words, chunk):
    txs = load_transactions(words, chunk)
    assert txs[0][0] == Op.LOAD_BEGIN and txs[-1][0] == Op.LOAD_END
    data = [b for t in txs[1:-1] for b in t[1:]]
    assert data == words_to_bytes(words)
    assert txs[-1][1:] == words_to_bytes([crc32_words(words)])


def test_read_id_parse():
    assert parse_read_id([0x60, 0x57, 0x50, 0x00, 0x01]) == (True, 1)


def test_host_refuses_other_architecture():
    words = [0xFAB0FAB1, 1 << 20]
    with pytest.raises(ArchMismatch):
        checked_load_transactions(words, ARCH_VERSION + 1, ARCH_VERSION)
    assert checked_load_transactions(words, ARCH_VERSION, ARCH_VERSION) == load_transactions(words)


def test_ch_write_flags():
    assert tx_ch_write(0xAB, last=True) == [Op.CH_WRITE, 1, 0xAB]

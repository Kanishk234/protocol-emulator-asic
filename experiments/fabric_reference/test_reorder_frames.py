import pytest

from frame_snapshot import HEADER, RECORD_BYTES, decode
from reorder_frames import ORDERS, clear_columns, reorder
from test_frame_snapshot import image


@pytest.mark.parametrize("order", ORDERS)
def test_addressed_payloads_preserved(order):
    original = image(0xAB000000)
    result = reorder(original, order)
    assert len(result) == len(original)
    assert result[:20] == HEADER
    assert result[-4:] == original[-4:]
    records = [result[i:i + RECORD_BYTES] for i in range(20, len(result) - 4, RECORD_BYTES)]
    # Reassemble by the actual encoded address, independently of permutation().
    records.sort(key=lambda record: int.from_bytes(record[:4], "big"))
    assert HEADER + b"".join(records) + result[-4:] == original
    assert result != original


def test_reject_invalid_input_or_order():
    with pytest.raises(ValueError):
        reorder(image(0)[:-4], "reverse")
    with pytest.raises(ValueError):
        reorder(image(0), "typo")
    with pytest.raises(ValueError):
        decode(reorder(image(0), "reverse"))


def test_clear_writes_all_frames_once_per_column():
    data = clear_columns()
    assert len(data) == 624
    assert data[:20] == HEADER
    assert data[-4:] == bytes.fromhex("00100000")
    seen = set()
    for start in range(20, len(data) - 4, 60):
        header = int.from_bytes(data[start:start + 4], "big")
        assert header & 0x07FFFFFF == 0x000FFFFF  # all frames; no desync/reserved bits
        seen.add(header >> 27)
        assert data[start + 4:start + 60] == bytes(56)
    assert seen == set(range(10))

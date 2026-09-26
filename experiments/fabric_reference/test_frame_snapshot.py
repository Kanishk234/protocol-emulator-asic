import pytest

from frame_snapshot import COLS, FRAMES, HEADER, ROWS, decode, snapshot, validate_header


def image(seed):
    # Distinct values expose row, column, frame and endianness mistakes.
    result = bytearray(HEADER)
    for col in range(COLS):
        for frame in range(FRAMES):
            result.extend(((col << 27) | (1 << frame)).to_bytes(4, "big"))
            for row in range(ROWS, 0, -1):
                result.extend((seed | col << 16 | frame << 8 | row).to_bytes(4, "big"))
    return bytes(result) + bytes.fromhex("00100000")


def test_snapshot_transition_and_row_order():
    old, new = image(0x12000000), image(0x34000000)
    values = snapshot(old, new, 33)
    for col in range(COLS):
        for row in range(1, ROWS + 1):
            for frame in range(FRAMES):
                seed = 0x34000000 if col * FRAMES + frame < 33 else 0x12000000
                assert values[col, row] >> (32 * frame) & 0xFFFFFFFF == seed | col << 16 | frame << 8 | row
    assert snapshot(old, new, 0) == snapshot(old, old, 200)
    assert snapshot(old, new, 200) == snapshot(new, new, 0)


@pytest.mark.parametrize("offset", [0, 20, 1220, -1])
def test_reject_corrupted_structure(offset):
    data = bytearray(image(0))
    data[offset] ^= 0x01
    with pytest.raises(ValueError):
        decode(bytes(data))


def test_reject_truncation_and_bad_count():
    data = image(0)
    with pytest.raises(ValueError):
        decode(data[:-4])
    with pytest.raises(ValueError):
        snapshot(data, data, 201)


def test_independent_header_validation():
    # Explicit all-zero payload, without the distinct-word image helper.
    data = bytearray(HEADER)
    macros = []
    for col in range(COLS):
        for frame in range(FRAMES):
            data.extend(((col << 27) | (1 << frame)).to_bytes(4, "big"))
            data.extend(bytes(4 * ROWS))
        for row in range(1, ROWS + 1):
            macros.append(f"`define Tile_X{col}Y{row}_Emulate_Bitstream 640'b" + "0" * 640)
    data.extend(bytes.fromhex("00100000"))
    header = "\n".join(macros)
    assert validate_header(bytes(data), header) == 140
    with pytest.raises(ValueError):
        validate_header(bytes(data), header[:-1] + "1")
    with pytest.raises(ValueError):
        validate_header(bytes(data), header + "\n" + macros[0])
    with pytest.raises(ValueError):
        validate_header(bytes(data), "")

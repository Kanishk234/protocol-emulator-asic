"""L1-PIN-RX, BITSYNC framing (milestone B2b, §14 P23, P24): RX bit stuffing and stuff errors, the RX CRC, words,
and FRAME n with its verdict. The line is CAN from the reference model in tools/protomodels/can.py (Bosch CAN
2.0: SOF..CRC-15 stuffed after 5 equal bits), which we did not write for this unit. The engine is set up as a CAN
receiver: STUFF_N 5, CRC-15 (poly 0x4599, init 0, residue 0 over SOF..CRC), 8-bit MSB-first words, IDLE_BITS 11,
and `FRAME [11] n` (n = the frame's SOF..CRC bit count) sent before each frame.

Expected tokens from P24: every 8 destuffed bits a DATA word, until bit n; at bit n the verdict carries the word so
far (P-G30: also when bit n completes it), EVENT `word[11:0]` if the CRC register equals CRC_RES, else ERR
`0x0www`. A stuff error is ERR `0x1nnn` with nnn = the index of the offending line bit in the frame (P-G27), and
the frame's words stop.
"""

import os

import cocotb

from pinlib import CTRL, DATA, ERR, EVENT, PAD, PinTb, ctrl, encode, enum, q8
from protomodels import can

UI0 = PAD["ui0"]
BS_TX, BS_RX = enum("txmode", "bitsync"), enum("rxmode", "bitsync")
FULL = int(os.environ.get("FULL", "0"))
PERIOD = 20


def cfg(**over):
    f = dict(txmode=BS_TX, rxmode=BS_RX, pin_a=UI0, idle=1, order=1, period=q8(PERIOD),
             sampleofs=round(0.75 * PERIOD * 256), sjw=q8(3), idle_bits=11, rx_nbits=8, nbits=7,
             stuff_n=5, crc_width=15, crc_poly=can.CRC15_POLY, crc_init=0, crc_res=0)
    f.update(over)
    return encode(**f)


def expected(fields, crc_good=True):
    """Tokens for one frame whose destuffed SOF..CRC bits are `fields` (P24, P-G30)."""
    n, toks, i = len(fields), [], 0
    while (i + 1) * 8 < n:
        toks.append((DATA, int("".join(map(str, fields[8 * i:8 * i + 8])), 2)))
        i += 1
    word = int("".join(map(str, fields[8 * i:n])), 2) & 0xFFF
    toks.append((EVENT, word) if crc_good else (ERR, word))
    return toks


async def send_frames(tb, frames, start):
    """frames: [(line bits, n)]; each preceded by FRAME [11] n. Returns the end clock."""
    t = start
    for bits, n in frames:
        tb.send(ctrl("FRAME", 1 << 11 | n), at=t - 40)
        for i, b in enumerate(bits):
            tb.drive(t + i * PERIOD, UI0, b)
        t += len(bits) * PERIOD
        tb.drive(t, UI0, 1)
        t += 14 * PERIOD
    return t


def got_tokens(tb):
    return [(tag, d) for _, tag, d in tb.loads]


@cocotb.test()
async def test_can_frames_words_and_verdict(dut):
    """Standard and extended CAN frames: destuffed words, and an EVENT verdict at FRAME's n (CRC good)."""
    tb = PinTb(dut)
    await tb.start(cfg(), pads=0xFFFFFF)
    frames, want = [], []
    for cid, data, ext in ((0x123, [0xDE, 0xAD], False), (0x1ABCDE, [1, 2, 3, 4, 5, 6, 7, 8], True),
                           (0x7FF, [0xFF, 0xFF, 0x00], False)):
        f = can.frame_fields(cid, data, ext=ext)
        frames.append((can.stuff(f) + [1] * 10, len(f)))
        want += expected(f)
    end = await send_frames(tb, frames, tb.n + 400)
    await tb.until(end + 40)
    if not FULL:
        assert got_tokens(tb) == []
        return
    assert got_tokens(tb) == want, (got_tokens(tb), want)
    assert tb.log[end]["ovr"] == 0 and tb.log[end]["late"] == 0


@cocotb.test()
async def test_can_bad_crc_and_stuff_error(dut):
    """A flipped CRC bit gives an ERR verdict; a stuff bit replaced by an equal bit is a stuff error (ERR
    0x1nnn) and stops that frame's words; the next frame is received normally."""
    if not FULL:
        return
    tb = PinTb(dut)
    await tb.start(cfg(), pads=0xFFFFFF)
    good = can.frame_fields(0x155, [0x0F, 0xF0])
    bad_crc = list(good)
    bad_crc[-3] ^= 1
    stuffed = can.stuff(can.frame_fields(0x0F0, [0x00, 0x00]))
    k = next(i for i in range(5, len(stuffed)) if all(stuffed[i - j] == stuffed[i - 1] for j in range(1, 6))
             and stuffed[i] != stuffed[i - 1])                  # the first stuff bit
    broken = stuffed[:k] + [stuffed[k - 1]] + stuffed[k + 1:]   # six equal bits: a stuff error at bit k
    destuffed_before = [b for i, b in enumerate(stuffed[:k])]   # all of them are data bits (no earlier stuffing)
    frames = [(can.stuff(bad_crc) + [1] * 10, len(bad_crc)),
              (broken + [1] * 10, len(can.frame_fields(0x0F0, [0, 0]))),
              (can.stuff(good) + [1] * 10, len(good))]
    end = await send_frames(tb, frames, tb.n + 400)
    await tb.until(end + 40)
    want = expected(bad_crc, crc_good=False)
    want += [(DATA, int("".join(map(str, destuffed_before[8 * i:8 * i + 8])), 2)) for i in range(k // 8)]
    want += [(ERR, 0x1000 | k)]
    want += expected(good)
    assert got_tokens(tb) == want, (got_tokens(tb), want)


@cocotb.test()
async def test_frame_now_late_and_setn_rx(dut):
    """FRAME without [11] with no frame in progress sets LATE (P24). SETN rx (applies at once in BITSYNC, P25)
    changes the word length for the next frame: 4-bit words."""
    if not FULL:
        return
    tb = PinTb(dut)
    await tb.start(cfg(), pads=0xFFFFFF)
    tb.send(ctrl("FRAME", 20), at=tb.n + 5)
    await tb.until(tb.n + 20)
    assert tb.log[-1]["late"] == 1
    tb.poke(tb.n + 1, clr_late=1)
    tb.send(ctrl("SETN", 1 << 5 | 4), at=tb.n + 10)
    f = can.frame_fields(0x321, [0x5A])
    end = await send_frames(tb, [(can.stuff(f) + [1] * 10, len(f))], tb.n + 400)
    await tb.until(end + 40)
    n = len(f)
    want, i = [], 0
    while (i + 1) * 4 < n:
        want.append((DATA, int("".join(map(str, f[4 * i:4 * i + 4])), 2)))
        i += 1
    want.append((EVENT, int("".join(map(str, f[4 * i:n])), 2) & 0xFFF))
    assert got_tokens(tb) == want, (got_tokens(tb), want)


@cocotb.test()
async def test_stuff_bit_right_after_n_is_checked(dut):
    """P24: after FRAME's n, stuffing stops, but a stuff bit due right after bit n is still removed and checked:
    a frame whose CRC ends in 5 equal bits, first with its stuff bit (no error), then with it violated (ERR
    0x1nnn after the verdict)."""
    if not FULL:
        return
    f = next(ff for ff in (can.frame_fields(cid, [d]) for cid in range(0, 0x7FF, 7) for d in range(0, 256, 17))
             if len(set(ff[-5:])) == 1 and len(set(can.stuff(ff)[-6:-1])) == 1)
    line = can.stuff(f)
    assert line[-1] != line[-2]                                   # the stuff bit after the CRC
    violated = line[:-1] + [line[-2]]
    tb = PinTb(dut)
    await tb.start(cfg(), pads=0xFFFFFF)
    end = await send_frames(tb, [(line + [1] * 10, len(f)), (violated + [1] * 10, len(f))], tb.n + 400)
    await tb.until(end + 40)
    want = expected(f) + expected(f) + [(ERR, 0x1000 | (len(line) - 1))]
    assert got_tokens(tb) == want, (got_tokens(tb), want)


@cocotb.test()
async def test_stuff_level_ones_only(dut):
    """P23 with STUFF_LVL = 1 (HDLC style, stuffing from protomodels.hdlc): only runs of five 1s get a stuff bit;
    runs of 0s do not. No CRC (the verdict is EVENT)."""
    if not FULL:
        return
    from protomodels import hdlc
    bits = [0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 1]
    line = hdlc.stuff(bits)
    assert len(line) > len(bits)
    tb = PinTb(dut)
    await tb.start(cfg(stuff_lvl=enum("stuff_lvl", 1), crc_width=0, idle_bits=7), pads=0xFFFFFF)
    end = await send_frames(tb, [(line + [1] * 10, len(bits))], tb.n + 400)
    await tb.until(end + 40)
    assert got_tokens(tb) == expected(bits), (got_tokens(tb), expected(bits))


@cocotb.test()
async def test_crc_skip(dut):
    """P24 CRC_SKIP: the RX CRC starts after the first 3 destuffed bits (a 3-bit header before a CRC-15 body)."""
    if not FULL:
        return
    head, body = [0, 1, 1], can.frame_fields(0x2A5, [0x3C])[:-15]
    f = head + body + [(can.crc15(body) >> (14 - i)) & 1 for i in range(15)]
    tb = PinTb(dut)
    await tb.start(cfg(crc_skip=3), pads=0xFFFFFF)
    end = await send_frames(tb, [(can.stuff(f) + [1] * 10, len(f))], tb.n + 400)
    await tb.until(end + 40)
    assert got_tokens(tb) == expected(f), (got_tokens(tb), expected(f))

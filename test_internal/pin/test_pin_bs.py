"""L1-PIN-RX, BITSYNC core (milestone B2a, §14 P20-P22): bit clock, bus idle, frame start with hard sync, resync
limited to SJW, and word framing of the sampled bits. Full units only; on a lean build the bitsync codes must
not receive anything (D-040).

The line is driven on ui0 by the test: NRZ frames, recessive = IDLE = 1, each frame's first bit dominant (0),
frames separated by idle. Words are RX_NBITS = 8, LSB first. Expected words are the frame's bytes; a partial
word at the frame end is dropped (P20: idle ends a frame without a verdict).
"""

import os
import random

import cocotb

from pinlib import DATA, PAD, PinTb, encode, enum, q8

UI0 = PAD["ui0"]
BS_TX, BS_RX = enum("txmode", "bitsync"), enum("rxmode", "bitsync")
FULL = int(os.environ.get("FULL", "0"))


def frame_bytes(rng, n, max_run=6):
    """n bytes whose line bits never hold more than max_run recessive samples in a row, the first bit dominant."""
    out = []
    for i in range(n):
        while True:
            b = rng.randrange(256)
            if i == 0 and b & 1:
                continue
            bits = [(x >> k) & 1 for x in out + [b] for k in range(8)]
            run = best = 0
            for v in bits:
                run = run + 1 if v else 0
                best = max(best, run)
            if best <= max_run:
                out.append(b)
                break
    return out


def line_bits(data, extra=()):
    return [(b >> k) & 1 for b in data for k in range(8)] + list(extra)


def cfg(period, sjw=0.0, sofs=0.7, idle_bits=8):
    return encode(txmode=BS_TX, rxmode=BS_RX, pin_a=UI0, idle=1, period=q8(period),
                  sampleofs=round(sofs * period * 256), sjw=q8(sjw), idle_bits=idle_bits, rx_nbits=8, nbits=7)


async def run_frames(tb, frames, cpb, start):
    """Drive frames (lists of bits) on ui0 at cpb clocks per bit, 12 idle bits between them; return the end."""
    t = start
    for bits in frames:
        tb.drive_bits(t, UI0, bits, cpb)
        t += int(len(bits) * cpb)
        tb.drive(t, UI0, 1)
        t += int(12 * cpb)
    return t


@cocotb.test()
async def test_bitsync_words_hard_sync_and_idle(dut):
    """Three frames at PERIOD = 20.5 clocks, each starting at a different clock phase: every byte arrives as a
    DATA word; the 3 trailing bits of the second frame are dropped at idle (IDLE_BITS = 5, so the idle line
    cannot complete that word first; P-G29: the sample that makes the bus idle is no frame bit)."""
    rng = random.Random(3)
    tb = PinTb(dut)
    await tb.start(cfg(20.5, idle_bits=5), pads=0xFFFFFF)
    f1, f2, f3 = frame_bytes(rng, 3, 4), frame_bytes(rng, 2, 4), frame_bytes(rng, 4, 4)
    frames = [line_bits(f1), line_bits(f2, extra=(0, 1, 0)), line_bits(f3)]
    await tb.until(40)
    end = await run_frames(tb, frames, 20.5, 300)             # after IDLE_BITS of idle line (P20)
    await tb.until(end + 50)
    got = [d for _, tag, d in tb.loads if tag == DATA]
    if not FULL:
        assert got == [], "a lean unit has no BITSYNC receiver (D-040)"
        return
    assert got == f1 + f2 + f3, (got, f1 + f2 + f3)
    assert tb.log[end]["ovr"] == 0


@cocotb.test()
async def test_bitsync_resync_under_clock_drift(dut):
    """P22: a sender 2 % fast, then 2 % slow, long frames (48 bits): with SJW = 0.15 PERIOD every word
    arrives; with SJW = 0 (hard sync only) the same line is misread."""
    if not FULL:
        return
    rng = random.Random(9)
    period = 24.0
    data = frame_bytes(rng, 6)
    tb = PinTb(dut)
    for i, (sjw, must_pass) in enumerate(((0.15 * period, True), (0.0, False))):
        if i == 0:
            await tb.start(cfg(period, sjw=sjw), pads=0xFFFFFF)
        else:
            await tb.write(cfg(period, sjw=sjw))            # a rewrite restarts the unit
        tb.loads.clear()
        base = tb.n + 300                                  # after IDLE_BITS of idle line (P20)
        end = await run_frames(tb, [line_bits(data), line_bits(data)], period * 0.98, base)
        end = await run_frames(tb, [line_bits(data)], period * 1.02, end + 40)
        await tb.until(end + 60)
        got = [d for _, tag, d in tb.loads if tag == DATA]
        if must_pass:
            assert got == data * 3, ("with resync", got)
        else:
            assert got != data * 3, "without resync a 2 % drift over 48 bits must break the reading"


@cocotb.test()
async def test_bitsync_resync_by_the_phase_error(dut):
    """P22: the bit start moves toward the edge by the phase error, limited to SJW. SJW = 0.3 PERIOD, sample at
    0.75: the sender stretches one bit per frame by 1 clock (its next edge is 1 clock late). Moving by the error
    (1 clock) keeps every sample in its bit; moving by the whole SJW would sample the following bit."""
    if not FULL:
        return
    rng = random.Random(21)
    period = 20
    tb = PinTb(dut)
    await tb.start(cfg(period, sjw=0.3 * period, sofs=0.75, idle_bits=5), pads=0xFFFFFF)
    want = []
    t = tb.n + 300
    for _ in range(4):
        data = frame_bytes(rng, 3, 4)
        bits = line_bits(data)
        late_at = rng.randrange(4, len(bits) - 4)
        while bits[late_at] == bits[late_at - 1]:        # the stretched bit must end in an edge
            late_at += 1
        for i, b in enumerate(bits):
            tb.drive(t + i * period + (1 if i >= late_at else 0), UI0, b)
        t += len(bits) * period + 1
        tb.drive(t, UI0, 1)
        t += 12 * period
        want += data
    await tb.until(t + 40)
    got = [d for _, tag, d in tb.loads if tag == DATA]
    assert got == want, (got, want)

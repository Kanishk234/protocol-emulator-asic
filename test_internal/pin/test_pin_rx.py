"""L1-PIN-RX and L1-OVR: the pin unit's RX half (ARCHITECTURE.md §4.5, §7.4, §14 P1, P2, P5, P8, P13,
P15, P18, P19).

A pad value driven for clock t is seen by the unit in clock t+2 (P1); a word or event is loaded at the
edge of the clock it completes in (P2), which is the `load` clock in the log.
"""

import cocotb

from pinlib import DATA, EVENT, PAD, PinTb, ctrl, encode, enum, q8

UI0, UI1, UI2, UIO0 = PAD["ui0"], PAD["ui1"], PAD["ui2"], PAD["uio0"]
SRX, LRX = enum("rxmode", "shift_rx"), enum("rxmode", "linked_rx")
PER, SOFS = q8(5.4), round(0.5 * q8(5.4))


def uart_bits(byte):
    return [0] + [byte >> i & 1 for i in range(8)] + [1]


def frame(byte):
    return 0x200 | byte << 1


@cocotb.test()
async def test_shift_rx_sample_points(dut):
    """P5: sample i in clock t0 + (SAMPLEOFS + i*PERIOD) >> 8. The pad holds the true bit only in the
    clock each sample reads (t - 2) and the opposite value elsewhere, so any off-by-one fails."""
    tb = PinTb(dut)
    await tb.start(encode(rxmode=SRX, idle=1, pin_a=UI0, period=PER, sampleofs=SOFS, rx_nbits=10,
                          autorearm=1))
    bits = uart_bits(0xB4)
    t0 = 22                                           # start bit at the pad in 20
    smp = [t0 + ((SOFS + i * PER) >> 8) for i in range(10)]
    tb.drive(20, UI0, 0)
    for c in range(21, smp[-1] - 1):
        nxt = next(i for i, s in enumerate(smp) if s - 2 >= c)
        tb.drive(c, UI0, bits[nxt] if smp[nxt] - 2 == c else 1 - bits[nxt])
    tb.drive(smp[-1] - 1, UI0, 1)
    await tb.until(smp[-1] + 20)
    assert tb.loads == [(smp[-1], DATA, frame(0xB4))]
    assert tb.log[-1]["ovr"] == 0


@cocotb.test()
@cocotb.parametrize(rearm=[1, 0])
async def test_shift_rx_back_to_back_and_autorearm(dut, rearm):
    """AUTOREARM: back-to-back frames (the next start bit right after the stop bit) all arrive; without
    it, SHIFT_RX stops after one word."""
    want = [0x5A, 0x00, 0xFF] if rearm else [0x5A]
    tb = PinTb(dut)
    await tb.start(encode(rxmode=SRX, idle=1, pin_a=UI0, period=PER, sampleofs=SOFS, rx_nbits=10,
                          autorearm=rearm))
    bits = sum((uart_bits(b) for b in (0x5A, 0x00, 0xFF)), [])
    tb.drive_bits(20, UI0, bits, PER / 256)
    await tb.until(20 + int(31 * PER / 256) + 10)
    assert [(t, d) for _, t, d in tb.loads] == [(DATA, frame(b)) for b in want]


def clocked(tb, clk_pad, dat_pad, bits, first, half=5):
    """Drive a clock (low, then high for `half` clocks per bit) with data changing while it is low:
    bit k is set in first + 2*half*k and the clock rises in first + 2*half*k + half.
    Returns the clocks in which the unit sees each rise and each fall."""
    rises, falls = [], []
    for k, b in enumerate(bits):
        t = first + 2 * half * k
        tb.drive(t, dat_pad, b)
        tb.drive(t + half, clk_pad, 1)
        tb.drive(t + 2 * half, clk_pad, 0)
        rises.append(t + half + 2)
        falls.append(t + 2 * half + 2)
    return rises, falls


def msb(bits):
    return sum(b << (len(bits) - 1 - i) for i, b in enumerate(bits))


@cocotb.test()
@cocotb.parametrize(edge_name=["rise", "fall"])
async def test_linked_rx_rise_and_fall(dut, edge_name):
    """LINKED_RX samples pin A on RX_EDGE of pin B: the same waveform read on the rise and on the fall
    (where the data has already moved on to the next bit)."""
    bits = [1, 0, 1, 1, 0, 0, 1, 0, 1]
    got = bits[:8] if edge_name == "rise" else bits[1:9]
    tb = PinTb(dut)
    await tb.start(encode(rxmode=LRX, rx_edge=enum("rx_edge", edge_name), order=1, pin_a=UI0,
                          pin_b=UI1, rx_nbits=8), pads=0xFFFFFD)
    rises, falls = clocked(tb, UI1, UI0, bits, 20)
    await tb.until(falls[-1] + 5)
    at = rises[7] if edge_name == "rise" else falls[7]
    assert tb.loads[0] == (at, DATA, msb(got))


@cocotb.test()
async def test_two_phase_framing(dut):
    """P13: RX_NBITS2 alternates the word length (8 + 1, as I2C data + ACK), words right-aligned."""
    tb = PinTb(dut)
    await tb.start(encode(rxmode=LRX, pin_a=UI0, pin_b=UI1, rx_nbits=8, rx_nbits2=1), pads=0xFFFFFD)
    b = [1, 1, 0, 1, 0, 0, 0, 1, 0] + [0, 1, 1, 1, 1, 0, 0, 1, 1]
    rises, _ = clocked(tb, UI1, UI0, b, 20)
    await tb.until(rises[-1] + 5)
    lsb = lambda bs: sum(x << i for i, x in enumerate(bs))
    assert tb.loads == [(rises[7], DATA, lsb(b[:8])), (rises[8], DATA, b[8]),
                        (rises[16], DATA, lsb(b[9:17])), (rises[17], DATA, b[17])]


@cocotb.test()
@cocotb.parametrize(echo=[0, 1])
async def test_echo_suppression(dut, echo):
    """P13: a word with a sample taken while our own shifted bit is on pin A is dropped when RX_ECHO = 0
    (framing still advances) and kept when RX_ECHO = 1."""
    if True:
        tb = PinTb(dut)
        await tb.start(encode(txmode=enum("txmode", "shift"), idle=1, pin_a=UIO0, period=q8(10), nbits=7,
                              rxmode=LRX, pin_b=UI1, rx_nbits=4, rx_echo=echo), pads=0xFFFFFD)
        tb.send((DATA, 0x3C), at=10)        # bits at edges 11 .. 81, IDLE again at 91
        for k in range(12):                  # pin B rises seen in 15 + 10k: words end at 45, 85, 125
            tb.drive(13 + 10 * k, UI1, 1)
            tb.drive(18 + 10 * k, UI1, 0)
        await tb.until(140)
        assert [c for c, _, _ in tb.loads] == ([45, 85, 125] if echo else [125])
        assert tb.loads[-1][2] == 0xF          # after the shift: our IDLE level


@cocotb.test()
async def test_event_timestamps(dut):
    """P8: EVENT {new level of A, tick[14:0]}, the tick counting PRESC clocks (D-024), on both edges."""
    tb = PinTb(dut)
    ticks = []
    await tb.start(encode(pin_a=UI0, ev_edge=enum("ev_edge", "both"), presc=3))
    tb.hook = lambda t: ticks.append(int(dut.u_unit.u_rx.tick.value))
    for c, v in ((100, 0), (137, 1), (300, 0)):
        tb.drive(c, UI0, v)
    await tb.until(320)
    steps = [b - a for a, b in zip(ticks, ticks[1:])]
    ups = [i for i, s in enumerate(steps) if s]
    assert set(steps) <= {0, 1} and all(b - a == 4 for a, b in zip(ups, ups[1:]))
    assert tb.loads == [(c, EVENT, v << 15 | ticks[c]) for c, v in ((102, 0), (139, 1), (302, 0))]


@cocotb.test()
async def test_qualified_start_stop_and_reset(dut):
    """I2C START/STOP from the event generator: EV_EDGE both on SDA, EV_QUAL = SCL high for 2 samples,
    EV_RESET restarts word framing (P8)."""
    tb = PinTb(dut)
    await tb.start(encode(rxmode=LRX, pin_a=UI0, pin_b=UI1, rx_nbits=8, rx_nbits2=1,
                          ev_edge=enum("ev_edge", "both"), ev_qual=enum("ev_qual", 1), ev_reset=1))
    tb.drive(20, UI0, 0)                         # START: SDA falls while SCL high -> seen 22
    tb.drive(25, UI1, 0)
    rises, _ = clocked(tb, UI1, UI0, [1, 0, 1], 30)   # three bits, then an interrupted byte
    tb.drive(61, UI0, 0)                         # SDA low while SCL is low (from 60): no event
    tb.drive(62, UI1, 1)                         # SCL high (seen 64)
    tb.drive(70, UI0, 1)                         # STOP: SDA rises while SCL high -> seen 72
    tb.drive(80, UI0, 0)                         # START again -> seen 82 (resets framing)
    tb.drive(85, UI1, 0)
    byte = [0, 1, 0, 1, 1, 0, 1, 0, 0]
    r2, _ = clocked(tb, UI1, UI0, byte, 90)
    tb.drive(200, UI1, 0)
    tb.drive(200, UI0, 1)                        # SDA and SCL change in one clock: SCL was low: none
    await tb.until(210)
    ev = [(c, d >> 15) for c, t, d in tb.loads if t == EVENT]
    assert ev == [(22, 0), (72, 1), (82, 0)]
    words = [(c, d) for c, t, d in tb.loads if t == DATA]
    lsb = sum(x << i for i, x in enumerate(byte[:8]))
    # rises 1..3 before the STOP; the STOP/START reset framing, so the next word is the byte
    assert words == [(r2[7], lsb), (r2[8], 0)]


@cocotb.test()
async def test_sample_and_setn_rx(dut):
    """P19: SAMPLE d samples pin A at cursor + d; P18: SETN rx sets the word length and restarts
    framing at the cursor (a partial word is discarded)."""
    tb = PinTb(dut)
    await tb.start(encode(pin_a=UI0, rx_nbits=3))
    tb.send(ctrl("SYNC"), ctrl("SAMPLE", 5), ctrl("SAMPLE", 5), ctrl("SAMPLE", 5), at=10)
    # SYNC 10 (cursor 11); SAMPLE at 16, 21, 26 (each taken when the previous is at <= n+1)
    # the unit sees the true bit only in each sample's clock (pad 2 clocks earlier), the opposite
    # value in every other clock, so a sample one clock off reads the wrong bit
    want = {16: 1, 21: 0, 26: 1}
    for c in range(12, 31):
        near = min(want, key=lambda s: abs(s - c))
        tb.drive(c - 2, UI0, want[c] if c in want else 1 - want[near])
    await tb.until(35)
    assert [t[0] for t in tb.takes] == [10, 11, 15, 20]
    assert tb.loads == [(26, DATA, 0b101)]
    # SETN rx 2 between two SAMPLEs: the first bit is discarded, then a 2-bit word
    tb.send(ctrl("SAMPLE", 3), ctrl("SETN", 1 << 5 | 2), ctrl("SAMPLE", 3), ctrl("SAMPLE", 3), at=40)
    for c in range(40, 70):
        tb.drive(c, UI0, 1)
    await tb.until_taken(8)
    await tb.settle(10)
    assert [(t, d) for _, t, d in tb.loads[1:]] == [(DATA, 0b11)]


@cocotb.test()
async def test_deselect_holds_framing(dut):
    """P15: while pin C is inactive, RX framing is held in reset and no samples are taken."""
    tb = PinTb(dut)
    await tb.start(encode(rxmode=LRX, pin_a=UI0, pin_b=UI1, pin_c=UI2, c_active=0, rx_nbits=8),
                   pads=0xFFFFF9)
    clocked(tb, UI1, UI0, [1, 1, 1], 20)         # 3 bits of an aborted byte
    tb.drive(55, UI2, 1)                          # deselect ...
    clocked(tb, UI1, UI0, [0, 0], 60)             # ... clocks while deselected are ignored
    tb.drive(85, UI2, 0)                          # select again
    byte = [0, 1, 1, 0, 1, 0, 0, 1]
    r, _ = clocked(tb, UI1, UI0, byte, 90)
    await tb.until(r[-1] + 5)
    assert tb.loads == [(r[7], DATA, sum(x << i for i, x in enumerate(byte)))]


@cocotb.test()
async def test_overrun_keeps_the_old_token(dut):
    """L1-OVR (§4.5): with the producer full, a new token is discarded, the old one kept, OVERRUN
    sticky until cleared."""
    tb = PinTb(dut)
    await tb.start(encode(pin_a=UI0, ev_edge=enum("ev_edge", "both")), sub_ready=False)
    tb.drive(20, UI0, 0)
    tb.drive(30, UI0, 1)
    await tb.until(40)
    assert [c for c, _, _ in tb.loads] == [22]
    assert tb.log[32]["ovr"] == 0 and tb.log[33]["ovr"] == 1 and tb.log[39]["ovr"] == 1
    assert int(dut.p_tok.value) & 0x8000 == 0          # still the first event (level 0)
    tb.poke(41, clr_overrun=1)
    tb.poke(41, sub_ready=1)
    tb.pokes[42]["sub_ready"] = 1
    tb.drive(50, UI0, 0)
    await tb.until(60)
    assert tb.log[42]["ovr"] == 0 and tb.log[59]["ovr"] == 0
    assert [c for c, _, _ in tb.loads] == [22, 52]


@cocotb.test()
async def test_event_beats_word(dut):
    """P19: one load per clock; an EVENT wins over a word completing in the same clock, and the word
    sets OVERRUN."""
    tb = PinTb(dut)
    await tb.start(encode(rxmode=LRX, pin_a=UI0, pin_b=UI1, rx_nbits=1, ev_edge=enum("ev_edge", "fall")),
                   pads=0xFFFFFD)
    tb.drive(20, UI1, 1)                  # a rise sampling A = 1: a word, no event
    tb.drive(25, UI1, 0)
    tb.drive(30, UI1, 1)
    tb.drive(30, UI0, 0)                  # A falls with the rise: event and word in clock 32
    await tb.until(40)
    assert tb.loads == [(22, DATA, 1), (32, EVENT, int(tb.loads[1][2]) & 0x7FFF)]
    assert tb.log[32]["ovr"] == 0 and tb.log[33]["ovr"] == 1

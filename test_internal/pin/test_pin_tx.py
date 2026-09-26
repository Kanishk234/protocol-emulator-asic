"""L1-PIN-TX: the pin unit's TX half (ARCHITECTURE.md §7.3, §14 P3, P4, P6, P9, P11, P12, P14-P16).

Every expected clock is derived in the test from the rules, with the log convention of pinlib: a token
taken in clock n acts at edge n+1 at the earliest (P3), and an action at edge k shows on the pad from
clock k+1.
"""

import cocotb

from pinlib import CTRL, DATA, EVENT, NONE, PAD, PinTb, ctrl, edge, encode, enum, level, q8

UO0, UIO0, UI0, UI1, UI2 = PAD["uo0"], PAD["uio0"], PAD["ui0"], PAD["ui1"], PAD["ui2"]
LVL, SHIFT, CLKGEN = (enum("txmode", m) for m in ("level", "shift", "clkgen"))


def waveform(actions, idle, since, until):
    """Expected pad value per clock from [(edge, value)], later entries winning an edge."""
    last = {}
    for e, v in actions:
        last[e] = v
    out, v = {}, idle
    for c in range(since, until):
        if c - 1 in last:
            v = last[c - 1]
        out[c] = v
    return out


def check_wave(tb, pad, expected):
    bad = [(c, tb.line(pad, c), v) for c, v in expected.items() if tb.line(pad, c) != v]
    assert not bad, f"pad {pad}: (clock, got, want) {bad[:8]}"


def shift_actions(start256, bits, period256):
    """P4: bit i changes the pad at edge (start + i * PERIOD) >> 8; returns (actions, end time)."""
    acts = [(edge(start256 + i * period256), b) for i, b in enumerate(bits)]
    return acts, start256 + len(bits) * period256


@cocotb.test()
async def test_level_delay_gap_late_sync(dut):
    """LEVEL/GAP/SYNC on the cursor with PRESC = 3 (P4); LATE only for a late LEVEL with a delay."""
    tb = PinTb(dut)
    await tb.start(encode(txmode=LVL, idle=1, pin_a=UO0, presc=2))
    tb.send(level(0), level(1, 5), ctrl("GAP", 4), level(0), at=10)
    await tb.until_taken(4)
    # cursor in the past: acts at the earliest edge, 11 (d = 0: not LATE); cursor := 11
    # LEVEL 1 +5 ticks: 11 + 15 = 26, taken at 11; GAP waits for P3 (26 <= n+1): taken at 25
    # GAP 4 ticks: cursor 38; LEVEL 0 taken at 26, acts at 38
    assert [t[0] for t in tb.takes] == [10, 11, 25, 26]
    await tb.until(60)
    check_wave(tb, UO0, waveform([(11, 0), (26, 1), (38, 0)], 1, 5, 60))
    assert tb.log[59]["late"] == 0

    tb.send(level(1, 5), at=100)            # cursor 38 + 15 = 53 < 101: late, acts at 101
    await tb.until(110)
    assert tb.takes[-1][0] == 100
    check_wave(tb, UO0, waveform([(101, 1)], 0, 60, 110))
    assert tb.log[100]["late"] == 0 and tb.log[101]["late"] == 1
    tb.poke(tb.n + 1, clr_late=1)
    tb.send(ctrl("SYNC"), level(0, 2), at=200)   # SYNC: cursor := 201; LEVEL at 201 + 6 = 207
    await tb.until(220)
    assert [t[0] for t in tb.takes[-2:]] == [200, 201]
    check_wave(tb, UO0, waveform([(207, 0)], 1, 110, 220))
    assert tb.log[219]["late"] == 0


@cocotb.test()
async def test_p3_same_edge_later_token_wins(dut):
    """A token is taken once pending actions are at <= n+1; two actions on one edge: the later wins."""
    tb = PinTb(dut)
    await tb.start(encode(txmode=LVL, idle=0, pin_a=UO0))
    tb.send(ctrl("SYNC"), level(1, 10), level(0, 0), level(1, 0), at=10)
    await tb.until(40)
    # SYNC at 10 (cursor 11); LEVEL 1 at 11 for edge 21; LEVEL 0 taken at 20 for edge 21 too;
    # LEVEL 1 taken at 21, cursor 21 is before the earliest edge 22: acts at 22
    assert [t[0] for t in tb.takes] == [10, 11, 20, 21]
    check_wave(tb, UO0, waveform([(22, 1)], 0, 5, 40))
    assert tb.log[39]["late"] == 0


@cocotb.test()
async def test_level_mode_data_and_event_drive_bit0(dut):
    """P12: in LEVEL mode a DATA or EVENT token drives data[0] at max(cursor, earliest)."""
    tb = PinTb(dut)
    await tb.start(encode(txmode=LVL, idle=1, pin_a=UO0))
    tb.send((DATA, 0x0002), (EVENT, 0x8001), (DATA, 0x0000), at=10)
    await tb.until(30)
    assert [t[0] for t in tb.takes] == [10, 11, 12]
    check_wave(tb, UO0, waveform([(11, 0), (12, 1), (13, 0)], 1, 5, 30))


@cocotb.test()
async def test_oe_and_open_drain(dut):
    """OE follows the cursor; with OD the pad is never driven high (1 releases, 0 drives low)."""
    tb = PinTb(dut)
    await tb.start(encode(txmode=SHIFT, idle=1, od=1, pin_a=UIO0, period=q8(3.5), nbits=7))
    tb.send((DATA, 0x5A), (DATA, 0xC3), ctrl("OE", 0 << 11 | 2), level(0), at=10)
    await tb.until_taken(4)
    await tb.settle(20)
    assert all(not (r["aoe"] and r["a"]) for r in tb.log), "open drain drove the pad high"
    assert all(r["a"] == 0 for r in tb.log)
    # released lines read the pull-up; every driven clock reads low
    t_oe = tb.takes[2][0]
    lows = [r["n"] for r in tb.log if r["aoe"]]
    assert lows and max(lows) < t_oe + 4
    assert tb.log[-1]["aoe"] == 0 and tb.line(UIO0, tb.n) == 1   # OE 0 wins over LEVEL 0


@cocotb.test()
async def test_uart_shift_fractional_back_to_back(dut):
    """SHIFT at PERIOD 5.4 clocks: bit edges at (start + i*PERIOD) >> 8, frames join with no gap (P4)."""
    per = q8(5.4)
    tb = PinTb(dut)
    await tb.start(encode(txmode=SHIFT, idle=1, pin_a=UO0, period=per, nbits=9))
    frames = [0x200 | 0x55 << 1, 0x200 | 0xA3 << 1, 0x200 | 0x0F << 1]
    tb.send(*[(DATA, f) for f in frames], at=20)
    await tb.until_taken(3)
    await tb.settle(80)
    start, acts, takes = 21 * 256, [], [20]
    for i, f in enumerate(frames):
        a, end = shift_actions(start, [f >> b & 1 for b in range(10)], per)
        acts += a
        if i + 1 < len(frames):
            takes.append(edge(end) - 1)     # P3: the return to IDLE is the last pending action
        start = end
    acts.append((edge(start), 1))
    assert [t[0] for t in tb.takes] == takes
    check_wave(tb, UO0, waveform(acts, 1, 10, tb.n))


@cocotb.test()
async def test_shift_4096_bits_drift_free(dut):
    """Fractional period over 4096 bits: every edge exact, mean = PERIOD, jitter <= 1 clock."""
    per = q8(5.4)
    tb = PinTb(dut)
    await tb.start(encode(txmode=SHIFT, idle=0, pin_a=UO0, period=per, nbits=15))
    tb.send(*[(DATA, 0x5555)] * 256, at=10)
    await tb.until_taken(256)
    await tb.settle(120)
    ch = [c for c, _ in tb.changes(UO0)]
    want = [edge(11 * 256 + i * per) + 1 for i in range(4096)]
    bad = [(i, a, b) for i, (a, b) in enumerate(zip(ch, want)) if a != b]
    assert not bad and len(ch) >= 4096, f"bit edges drift: (bit, got, want) {bad[:5]}, {len(ch)} edges"
    gaps = [b - a for a, b in zip(ch, ch[1:4096])]
    assert set(gaps) <= {5, 6}
    assert abs((ch[4095] - ch[0]) / 4095 - per / 256) < 1e-3


@cocotb.test()
async def test_msb_order_setn_and_length_in_token(dut):
    """ORDER msb, SETN tx n (n = 0 means 16), and TX_LENTOK length in data[15:12] (P14)."""
    tb = PinTb(dut)
    await tb.start(encode(txmode=SHIFT, idle=0, order=1, pin_a=UO0, period=q8(4), nbits=7))
    tb.send(ctrl("SETN", 4), (DATA, 0b1011), ctrl("SETN", 0), (DATA, 0x8001), at=10)
    await tb.until_taken(4)
    await tb.settle(90)
    # SETN at 10, DATA at 11 (start 12); SETN 0 and the next DATA wait for P3, and a DATA shift starts
    # at max(cursor, earliest) (P4)
    s1 = (tb.takes[1][0] + 1) * 256
    a1, e1 = shift_actions(s1, [1, 0, 1, 1], 1024)
    t3 = tb.takes[3][0]
    assert tb.takes[2][0] == edge(e1) - 1 and t3 == edge(e1)
    a2, e2 = shift_actions(max(e1, (t3 + 1) * 256), [1] + [0] * 14 + [1], 1024)
    check_wave(tb, UO0, waveform(a1 + [(edge(e1), 0)] + a2 + [(edge(e2), 0)], 0, 10, tb.n))

    # the same unit, re-configured: TX_LENTOK, LSB first
    await tb.write(encode(txmode=SHIFT, idle=0, tx_lentok=1, pin_a=UO0, period=q8(4), nbits=7))
    tb.send((DATA, 2 << 12 | 0b110), at=tb.n + 5)
    await tb.until_taken(5)
    await tb.settle(20)
    t = tb.takes[4][0]
    a, e = shift_actions((t + 1) * 256, [0, 1, 1], 1024)
    check_wave(tb, UO0, waveform(a + [(edge(e), 0)], 0, t, tb.n))


@cocotb.test()
async def test_clkgen_periods_extension_odd_period(dut):
    """CLK n: IDLE half then ACTIVE half each period (P11); a CLK taken during a burst extends it."""
    tb = PinTb(dut)
    await tb.start(encode(txmode=CLKGEN, idle=0, pin_a=UO0, period=q8(6)))
    tb.send(ctrl("CLK", 3), ctrl("CLK", 2), level(1), at=10)
    await tb.until_taken(3)
    await tb.settle(20)
    # start 11; ACTIVE at 11 + 3 + 6k, release at 11 + 6 + 6k, k = 0..4 (3 + 2 periods, seamless)
    acts = []
    for k in range(5):
        acts += [(14 + 6 * k, 1), (17 + 6 * k, 0)]
    end = 17 + 6 * 4
    assert tb.takes[1][0] == 11                      # extension taken while the burst runs
    assert tb.takes[2][0] == end - 1                 # other tokens: P3 at the final release
    check_wave(tb, UO0, waveform(acts + [(end, 1)], 0, 5, tb.n))

    # PERIOD 5 (halves of 2.5 clocks): ACTIVE at floor(s + 2.5 + 5k), release at s + 5 + 5k
    await tb.write(encode(txmode=CLKGEN, idle=0, pin_a=UO0, period=q8(5)))
    t0 = tb.n + 5
    tb.send(ctrl("CLK", 2), at=t0)
    await tb.until(t0 + 30)
    s = t0 + 1
    check_wave(tb, UO0, waveform([(s + 2, 1), (s + 5, 0), (s + 7, 1), (s + 10, 0)], 0, t0, t0 + 30))


@cocotb.test()
async def test_clkgen_stretch(dut):
    """STRETCH (P11): after a release the IDLE half starts in the first clock pin A reads IDLE."""
    tb = PinTb(dut)
    await tb.start(encode(txmode=CLKGEN, idle=1, od=1, stretch=1, pin_a=UIO0, period=q8(10)))
    tb.drive(20, UIO0, 0)                  # a target holds SCL low over our release (edge 21) ...
    tb.drive(41, UIO0, 1)                  # ... until clock 41
    tb.send(ctrl("CLK", 2), level(0), at=10)
    await tb.until(90)
    # start 11: IDLE; ACTIVE (low) at 16; release at 21. The line reads high in clock 41, the unit
    # sees it in 43 (P1): IDLE half from 43, ACTIVE at 48, release at 53; the line is high from 54,
    # seen in 56: the burst ends there (cursor := 56), and LEVEL 0 is taken in 56 and acts at 57.
    drv = [r["n"] for r in tb.log if r["aoe"]]
    want = list(range(17, 22)) + list(range(49, 54)) + list(range(58, len(tb.log)))
    assert drv == want, (drv, tb.takes)
    assert tb.takes[1][0] == 56


@cocotb.test()
async def test_wait_for_pin_b_edge(dut):
    """WAIT (P16): no tokens until pin B shows the edge; then cursor := earliest."""
    tb = PinTb(dut)
    await tb.start(encode(txmode=LVL, idle=1, pin_a=UO0, pin_b=UI0))
    tb.drive(15, UI0, 0)                    # pin B falls (seen in 17): not the edge WAIT asks for
    tb.drive(20, UI0, 1)                    # pin B rises at the pad in clock 20, seen in 22
    tb.send(ctrl("WAIT", 1), level(0, 3), at=5)
    await tb.until(40)
    assert [t[0] for t in tb.takes] == [5, 22]      # P-G8: taken in the edge clock
    check_wave(tb, UO0, waveform([(26, 0)], 1, 5, 40))


def sck_falls(tb, pad, first_high, n, half=4):
    """Drive a clock on `pad`: high from first_high + 2*half*k for `half` clocks, n periods."""
    for k in range(n):
        tb.drive(first_high + 2 * half * k, pad, 1)
        tb.drive(first_high + 2 * half * k + half, pad, 0)
    return [first_high + 2 * half * k + half + 2 for k in range(n)]   # clocks the unit sees each fall


@cocotb.test()
async def test_linked_preload_and_join(dut):
    """Linked TX on SCK fall with TX_PRELOAD (P6, P9): bit 0 at once, then one bit per fall; the next
    byte's bit 0 replaces the return to IDLE."""
    tb = PinTb(dut)
    await tb.start(encode(txmode=SHIFT, idle=1, order=1, nbits=7, tx_preload=1, pin_a=UO0, pin_b=UI1,
                          tx_edge=enum("tx_edge", "fall")), pads=0xFFFFFD)
    falls = sck_falls(tb, UI1, 20, 17)
    tb.send((DATA, 0xA5), (DATA, 0x3C), at=5)
    await tb.until(falls[-1] + 5)
    b1 = [0xA5 >> (7 - i) & 1 for i in range(8)]
    b2 = [0x3C >> (7 - i) & 1 for i in range(8)]
    acts = [(6, b1[0])] + [(falls[k], b1[k + 1]) for k in range(7)]
    acts += [(falls[7 + k], b2[k]) for k in range(8)] + [(falls[15], 1)]
    assert tb.takes[0][0] == 5
    assert tb.takes[1][0] == falls[6] + 1            # as soon as all bits of the first byte are out
    check_wave(tb, UO0, waveform(acts, 1, 2, tb.n))


@cocotb.test()
async def test_linked_select_abort_and_c_oe(dut):
    """Pin C (P15): C_OE gates the output one clock after the synchronised change; deselect aborts
    a linked shift (pin A back to IDLE at that clock's edge); a preload made while deselected waits."""
    tb = PinTb(dut)
    await tb.start(encode(txmode=SHIFT, idle=1, order=1, nbits=7, tx_preload=1, pin_a=UIO0, pin_b=UI1,
                          tx_edge=enum("tx_edge", "fall"), pin_c=UI2, c_active=0, c_oe=1),
                   pads=0xFFFFFD)
    tb.send((DATA, 0x00), at=5)            # taken while deselected: bit 0 (0) preloaded
    tb.drive(15, UI2, 0)                    # select: seen in 17, OE on from 18
    falls = sck_falls(tb, UI1, 20, 3)
    tb.drive(40, UI2, 1)                    # deselect mid-byte: seen in 42
    tb.drive(50, UI2, 0)                    # re-select
    tb.send((DATA, 0xFF), at=55)
    await tb.until(70)
    assert [r["aoe"] for r in tb.log[10:25]] == [0] * 8 + [1] * 7
    assert tb.log[42]["aoe"] == 1 and tb.log[43]["aoe"] == 0
    assert tb.log[42]["a"] == 0 and tb.log[43]["a"] == 1    # aborted: IDLE at edge 42
    # re-selected: the next byte starts clean with its own preload
    assert tb.takes[-1][0] == 55
    assert all(tb.log[c]["a"] == 1 for c in range(57, 70))


@cocotb.test()
async def test_ignored_tokens(dut):
    """ERR tokens, unknown ops and BITSYNC-only ops on a lean unit are taken and ignored (P4)."""
    tb = PinTb(dut)
    await tb.start(encode(txmode=LVL, idle=1, pin_a=UO0))
    tb.send((3, 0x0000), (CTRL, 0xF123), ctrl("FRAME", 5), ctrl("LINE", 0x10), ctrl("JAM", 0x123),
            ctrl("CLK", 4), level(0), at=10)
    await tb.until(30)
    assert [t[0] for t in tb.takes] == list(range(10, 17))
    check_wave(tb, UO0, waveform([(17, 0)], 1, 5, 30))

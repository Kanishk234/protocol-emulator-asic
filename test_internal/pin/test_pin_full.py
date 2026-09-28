"""L1-PIN-TX for the full units' features (milestone B, D-040): PULSE (§14 P17) and the carrier (P30).

On a lean build (FULL=0) the same configurations must fall back as D-040 says: the PULSE code acts as LEVEL,
and the carrier fields are not stored. Expected clocks come from the rule text with pinlib's convention: a
token taken in clock n acts at edge n+1 at the earliest (P3); an action at edge k shows from clock k+1.
Readings of open points are marked P-G24 (a 0-tick phase lasts one clock) and P-G26 (carrier edges at
t + floor(k * CARRIER / 2), CARRIER in 1/256 clocks).
"""

import os

import cocotb

from pinlib import DATA, PAD, PinTb, ctrl, encode, enum, level, q8

UO0 = PAD["uo0"]
LVL, PULSE = enum("txmode", "level"), enum("txmode", "pulse")
FULL = int(os.environ.get("FULL", "0"))


def waveform(actions, idle, since, until):
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


def pulse_actions(start, bits, sym, tick):
    """P17: bit b drives SYMb_FIRST at t, the other level at t + T1 * tick, the next bit at
    t + (T1 + T2) * tick (a 0-tick phase: 1 clock, P-G24). Returns (actions, end edge)."""
    acts, t = [], start
    for b in bits:
        first, t1, t2 = sym[b]
        d1 = t1 * tick if t1 else 1
        d2 = t2 * tick if t2 else 1
        acts += [(t, first), (t + d1, 1 - first)]
        t += d1 + d2
    return acts, t


def bits_of(value, n, msb=False):
    b = [(value >> i) & 1 for i in range(n)]
    return b[::-1] if msb else b


@cocotb.test()
async def test_pulse_symbols_and_back_to_back(dut):
    """Two 8-bit PULSE tokens, PRESC = 1 (a tick is 2 clocks): every edge where P17 puts it, the second
    token's first bit on the first token's end edge (no gap), IDLE after the last bit, no LATE."""
    tb = PinTb(dut)
    sym = {0: (1, 3, 5), 1: (1, 6, 2)}             # (FIRST, T1, T2) per bit value
    await tb.start(encode(txmode=PULSE, idle=0, pin_a=UO0, presc=1, nbits=7,
                          sym0_first=1, sym0_t1=3, sym0_t2=5, sym1_first=1, sym1_t1=6, sym1_t2=2))
    tb.send((DATA, 0xA5), (DATA, 0x3C), at=10)
    await tb.until_taken(2)
    if not FULL:                                   # D-040: lean units treat PULSE as LEVEL (data[0])
        await tb.until(40)
        check_wave(tb, UO0, waveform([(11, 1), (12, 0)], 0, 5, 40))
        return
    a1, end1 = pulse_actions(11, bits_of(0xA5, 8), sym, 2)
    a2, end2 = pulse_actions(end1, bits_of(0x3C, 8), sym, 2)
    await tb.until(end2 + 20)
    check_wave(tb, UO0, waveform(a1 + a2 + [(end2, 0)], 0, 5, end2 + 20))
    assert tb.takes[1][0] <= end1 - 1, "the second token must be taken in time to join"
    assert tb.log[end2 + 10]["late"] == 0


@cocotb.test()
async def test_pulse_msb_order_gap_and_zero_phase(dut):
    """MSB order, PRESC = 0, a GAP after the token (cursor = the end time, P17), and a 0-tick second phase
    (one clock, P-G24)."""
    if not FULL:
        return
    tb = PinTb(dut)
    sym = {0: (0, 4, 0), 1: (0, 1, 3)}
    await tb.start(encode(txmode=PULSE, idle=1, pin_a=UO0, order=1, nbits=3,
                          sym0_first=0, sym0_t1=4, sym0_t2=0, sym1_first=0, sym1_t1=1, sym1_t2=3))
    tb.send((DATA, 0x6), ctrl("GAP", 10), level(0), at=10)
    await tb.until_taken(3)
    acts, end = pulse_actions(11, bits_of(0x6, 4, msb=True), sym, 1)
    await tb.until(end + 30)
    check_wave(tb, UO0, waveform(acts + [(end, 1), (end + 10, 0)], 1, 5, end + 30))


@cocotb.test()
async def test_carrier_integer_and_fractional(dut):
    """P30: while pin A is not IDLE it toggles with period CARRIER (50 %), restarting at every change to the
    active level. 10 clocks, then 7.5 clocks (half 3.75: edges at t + floor(k * 3.75), P-G26); IDLE is
    steady; a second activation restarts the phase."""
    tb = PinTb(dut)
    await tb.start(encode(txmode=LVL, idle=0, pin_a=UO0, carrier=q8(10)))
    tb.send(level(1, 0), level(0, 23), level(1, 10), level(0, 12), at=10)
    await tb.until(120)
    if not FULL:                                   # lean: no carrier, plain levels
        check_wave(tb, UO0, waveform([(11, 1), (34, 0), (44, 1), (56, 0)], 0, 5, 120))
        return
    acts = [(11, 1)] + [(11 + 5 * k, k % 2 == 0) for k in range(1, 5)] + [(34, 0)]
    acts += [(44, 1)] + [(44 + 5 * k, k % 2 == 0) for k in range(1, 3)] + [(56, 0)]
    check_wave(tb, UO0, waveform([(e, int(v)) for e, v in acts], 0, 5, 120))

    await tb.write(encode(txmode=LVL, idle=0, pin_a=UO0, carrier=q8(7.5)))   # a rewrite restarts the unit
    start = tb.n + 10
    tb.send(level(1, 0), level(0, 40), at=start)
    await tb.until(start + 60)
    t = start + 1
    half = q8(7.5)                                  # CARRIER / 2 in 1/512 clocks
    acts = [(t, 1)] + [(t + (k * half) // 512, k % 2 == 0) for k in range(1, 11) if (k * half) // 512 < 40]
    acts += [(t + 40, 0)]
    check_wave(tb, UO0, waveform([(e, int(v)) for e, v in acts], 0, start, start + 60))


@cocotb.test()
async def test_carrier_on_a_pulse_stream(dut):
    """IR-NEC style: PULSE marks at the active level are modulated, spaces are steady IDLE (P30 applies to any
    TXMODE); each mark restarts the carrier phase."""
    if not FULL:
        return
    tb = PinTb(dut)
    await tb.start(encode(txmode=PULSE, idle=0, pin_a=UO0, nbits=1, carrier=q8(6),
                          sym0_first=1, sym0_t1=9, sym0_t2=7, sym1_first=1, sym1_t1=9, sym1_t2=13))
    tb.send((DATA, 0x1), at=10)                     # bits 1, 0 (LSB first)
    await tb.until(80)
    acts = []
    for mark in (11, 11 + 9 + 13):                  # each mark: 9 clocks on, toggling every 3
        acts += [(mark + 3 * k, int(k % 2 == 0)) for k in range(0, 3)] + [(mark + 9, 0)]
    check_wave(tb, UO0, waveform(acts, 0, 5, 80))

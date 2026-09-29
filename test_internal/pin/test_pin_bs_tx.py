"""L1-PIN-TX, BITSYNC transmit (milestone B2c, §14 P21, P22, P25): the TX queue with SYNC and LINE, TX stuffing,
the TX CRC, WAIT [1], joining another node's frame, and the own-edge rules.

Pin A is on a bidirectional pad with OD = 1 and IDLE = 1, so the pad is a wired-AND bus: the unit pulls it low for
a dominant bit and releases it otherwise; the other node (`pads_ext`) does the same. The unit senses the same pad
(no pin S), so it receives its own frames.

The main check is end to end against a reference we did not write for this unit: `tools/protomodels/can.py`'s
CANNode (Bosch CAN 2.0, clock-level, with its own bit timing, destuffing, CRC-15 check and ACK) sits on the bus and
must decode our frames and ACK them. The other tests use `tools/protomodels/hdlc.py`'s bit stuffing and a CRC
written here from the definition (MSB-first LFSR).

Expected values from P25: after SYNC, the queued bits start a frame at the first bit boundary after bus idle (our
first bit on the line from the clock after that edge; EVENT 0x9001 loaded at that edge). With an integer PERIOD our
bit i then occupies clocks s+1+PERIOD*i .. s+PERIOD*(i+1), with no drift: the unit never resyncs on the echo of its
own edges (P22) and the echo of its first bit is no frame start (P21).
"""

import os

import cocotb

from pinlib import CTRL, DATA, ERR, EVENT, PAD, PinTb, ctrl, encode, enum, level, q8
from protomodels import can, hdlc

BUS = PAD["uio0"]
BS_TX, BS_RX = enum("txmode", "bitsync"), enum("rxmode", "bitsync")
FULL = int(os.environ.get("FULL", "0"))
PERIOD = 20
START = (EVENT, 0x9001)


def cfg(**over):
    f = dict(txmode=BS_TX, rxmode=BS_RX, pin_a=BUS, od=1, idle=1, order=1, tx_lentok=1, period=q8(PERIOD),
             sampleofs=q8(15), sjw=q8(3), idle_bits=11, rx_nbits=8, nbits=7,
             stuff_n=5, crc_width=15, crc_poly=can.CRC15_POLY, crc_init=0, crc_res=0)
    f.update(over)
    return encode(**f)


def line_op(stuff=False, crc_reset=False, crc_append=False):
    return ctrl("LINE", crc_reset << 6 | crc_append << 3 | stuff << 2)


def chunks(bits, k=12):
    """DATA tokens with the length in the token (TX_LENTOK), MSB first."""
    return [(DATA, (len(bits[i:i + k]) - 1) << 12 | int("".join(map(str, bits[i:i + k])), 2))
            for i in range(0, len(bits), k)]


def expected_rx(fields, crc_good=True, w=8, own=True):
    """RX tokens for one frame of destuffed bits `fields` with FRAME n = len(fields) (P24, P-G30); a good
    verdict carries data[14] = our own frame."""
    n, toks, i = len(fields), [], 0
    while (i + 1) * w < n:
        toks.append((DATA, int("".join(map(str, fields[w * i:w * i + w])), 2)))
        i += 1
    word = int("".join(map(str, fields[w * i:n])), 2) & 0xFFF
    return toks + [(EVENT, own << 14 | word) if crc_good else (ERR, word)]


def crc_msb(bits, poly, init, width):
    c = init
    for b in bits:
        top = (c >> (width - 1)) & 1
        c = (c << 1) & ((1 << width) - 1)
        if top ^ b:
            c ^= poly
    return c


def got(tb):
    return [(tag, d) for _, tag, d in tb.loads]


def starts(tb):
    return [n for n, tag, d in tb.loads if (tag, d) == START]


def bits_at(tb, s, count, first=None):
    """The bus level at the middle of our bits 0..count-1 of a frame whose first bit starts after edge s."""
    first = s + 1 if first is None else first
    return [tb.line(BUS, first + PERIOD * i + PERIOD // 2) for i in range(count)]


def can_frame_tokens(fields):
    n = len(fields)
    return [ctrl("FRAME", 1 << 11 | n), ctrl("SYNC"), line_op(stuff=True, crc_reset=True), *chunks(fields[:-15]),
            line_op(stuff=True, crc_append=True), line_op(), (DATA, 9 << 12 | 0x3FF)]


def bus_node(node):
    """A hook that puts a clock-level reference node on the bus (it sees the bus one clock late)."""
    def hook(tb):
        bus = tb.log[-1]["line"] >> BUS & 1 if tb.log else 1
        tb.drive(tb.n, BUS, node.step(bus))
    return hook


@cocotb.test()
async def test_can_frames_to_a_reference_node(dut):
    """Three CAN frames sent with SYNC / LINE / DATA and the TX CRC: a reference CAN node decodes each one (CRC
    good) and ACKs it. Every one of our bits lies at s+1+20i on the bus (no drift from our own echo); our own RX
    reports the start, the words and an EVENT verdict. The third frame's CRC ends in 5 equal bits, so a stuff bit
    is due after it and must go out before the `LINE` that stops stuffing (P25)."""
    if not FULL:
        return
    post = next((cid, [d]) for cid in range(0, 0x7FF, 7) for d in range(0, 256, 17)
                if len(set(can.frame_fields(cid, [d])[-5:])) == 1
                and len(set(can.stuff(can.frame_fields(cid, [d]))[-6:-1])) == 1)
    frames = [(0x123, [0xDE, 0xAD], False), (0x1ABCDE, [1, 2, 3, 4, 5, 6, 7, 8], True), (post[0], post[1], False)]
    node = can.CANNode(PERIOD, sp=0.75)
    tb = PinTb(dut)
    await tb.start(cfg(), pads=0xFFFFFF)
    tb.hook = bus_node(node)
    toks, fields = [], []
    for cid, data, ext in frames:
        f = can.frame_fields(cid, data, ext=ext)
        fields.append(f)
        toks += can_frame_tokens(f)
    tb.send(*toks, at=tb.n + 5)
    await tb.until_taken(len(toks))
    while len(node.received) < 3 and tb.n < 40000:
        await tb.settle(100)
    await tb.settle(40)
    assert [(r["id"], r["data"], r["ext"], r["crc_ok"]) for r in node.received] == \
        [(cid, data, ext, True) for cid, data, ext in frames], node.received
    assert node.errors == [], node.errors
    s = starts(tb)
    assert len(s) == 3, tb.loads
    want = []
    for f, s0 in zip(fields, s):
        line = can.stuff(f)
        assert bits_at(tb, s0, len(line) + 3) == line + [1, 0, 1], f"frame at {s0}"
        ours = [c for c, _ in tb.changes(BUS, s0) if c <= s0 + PERIOD * len(line)]
        assert ours and all((c - s0 - 1) % PERIOD == 0 for c in ours), (s0, ours)
        want += [START] + expected_rx(f)
    assert got(tb) == want, (got(tb), want)
    assert tb.log[-1]["ovr"] == 0 and tb.log[-1]["late"] == 0


@cocotb.test()
async def test_ones_stuffing_crc_xor_and_stuff_before_line(dut):
    """HDLC-style TX: ORDER = LSB first, NBITS 8, ones-only stuffing (STUFF_LVL 1), a CRC-16 (0x1021, init 0xFFFF)
    appended XOR CRC_XOR 0xFFFF. The payload is chosen so that the CRC ends in five 1s: the stuff 0 goes out
    before the `LINE` that turns stuffing off, then the flag 0x7E unstuffed. The line is compared with
    protomodels.hdlc's stuffing of data + CRC. With DELIM = flag (P27) our RX reports the four words, and the flag
    closes the frame with a good CRC (residue 0x1D0F): EVENT with data[14] = our own frame. (B2c's version had no
    DELIM and expected a stuff error at the flag; since B3 that error would stop our own TX, P26.)"""
    if not FULL:
        return

    def body(data):
        bits = hdlc.bits_of(data)
        c = crc_msb(bits, 0x1021, 0xFFFF, 16) ^ 0xFFFF
        return bits + [(c >> (15 - i)) & 1 for i in range(16)]

    data = next([0xA5, d] for d in range(256) if body([0xA5, d])[-5:] == [1] * 5
                and hdlc.stuff(body([0xA5, d]))[-1] == 0 and hdlc.stuff(body([0xA5, d]))[-6:-1] == [1] * 5)
    b = body(data)
    line = hdlc.stuff(b)
    tb = PinTb(dut)
    await tb.start(cfg(order=0, tx_lentok=0, stuff_lvl=enum("stuff_lvl", 1), crc_width=16, crc_poly=0x1021,
                       crc_init=0xFFFF, crc_xor=0xFFFF, crc_res=0x1D0F, idle_bits=11,
                       delim=enum("delim", "flag")), pads=0xFFFFFF)
    toks = [ctrl("SYNC"), line_op(stuff=True, crc_reset=True), (DATA, data[0]), (DATA, data[1]),
            line_op(stuff=True, crc_append=True), line_op(), (DATA, 0x7E)]
    tb.send(*toks, at=tb.n + 5)
    await tb.until_taken(len(toks))
    await tb.settle(PERIOD * 24)
    s = starts(tb)
    assert len(s) == 1, tb.loads
    sent = bits_at(tb, s[0], len(line) + 8 + 2)
    assert sent == line + hdlc.FLAG + [1, 1], (sent, line + hdlc.FLAG)
    words = [sum(b[8 * k + i] << i for i in range(8)) for k in range(4)]
    assert got(tb) == [START] + [(DATA, w) for w in words] + [(EVENT, 0x4000)], got(tb)


@cocotb.test()
async def test_no_idle_while_driving_ignored_ops_and_wait(dut):
    """P20: a run of 16 recessive bits we send inside our frame (no stuffing, IDLE_BITS 8) does not make the bus
    idle: all words and the verdict arrive. P25: LEVEL, OE, GAP, CLK, SAMPLE, SETN without bit 5, WAIT without [1],
    EVENT and ERR tokens are taken and ignored (the line stays released). WAIT [1] holds the next token until the
    next sample point, and it is taken in that clock (P-G31)."""
    if not FULL:
        return
    tb = PinTb(dut)
    await tb.start(cfg(stuff_n=0, crc_width=0, idle_bits=8, tx_lentok=0), pads=0xFFFFFF)
    smp = {}

    def probe(t):
        smp[t.n] = int(dut.u_unit.g_bs.u_bs.smp.value)
    tb.hook = probe
    toks = [ctrl("FRAME", 1 << 11 | 32), ctrl("SYNC"), (DATA, 0x0F), (DATA, 0xFF), (DATA, 0xF0), (DATA, 0x5A)]
    tb.send(*toks, at=tb.n + 5)
    await tb.until_taken(len(toks))
    await tb.settle(PERIOD * 14)
    assert got(tb) == [START, (DATA, 0x0F), (DATA, 0xFF), (DATA, 0xF0), (EVENT, 0x405A)], got(tb)
    s = starts(tb)[0]
    bits = [int(c) for c in "00001111111111111111000001011010"]
    assert bits_at(tb, s, 33) == bits + [1]

    ignored = [level(0), ctrl("OE", 0), ctrl("GAP", 50), ctrl("CLK", 3), ctrl("SAMPLE", 0), ctrl("SETN", 3),
               ctrl("WAIT", 1), (EVENT, 0x123), (ERR, 0x456)]
    t0 = tb.n
    tb.send(*ignored, at=t0 + 1)
    await tb.until_taken(len(toks) + len(ignored))
    await tb.settle(PERIOD * 3)
    assert all(r["line"] >> BUS & 1 for r in tb.log[t0:]), "an ignored op drove the line"
    assert len(tb.loads) == 5

    for _ in range(3):
        k = len(tb.takes)
        tb.send(ctrl("WAIT", 2), ctrl("CLK", 1), at=tb.n + 7)
        await tb.until_taken(k + 2)
        tw, tn = tb.takes[k][0], tb.takes[k + 1][0]
        first = next(c for c in range(tw + 1, tn + PERIOD * 2) if smp.get(c))
        assert tn == first, (tw, tn, first)
        await tb.settle(PERIOD // 3)


@cocotb.test()
async def test_join_another_nodes_frame_start(dut):
    """P21: our SYNC frame waits for bus idle; another node's first (dominant) bit arrives after the bus goes idle
    but before our first bit boundary. Our first bit is dominant, so we join that bit: EVENT 0x9001 in the
    frame-start clock, our pin A driven from its edge, and our following bits on the bit clock hard-synced to that
    edge. Our RX receives our frame (words and EVENT verdict)."""
    if not FULL:
        return
    f = can.frame_fields(0x2B3, [0x11, 0x22])
    line = can.stuff(f)
    tb = PinTb(dut)
    await tb.start(cfg(), pads=0xFFFFFF)
    seen = {}

    def other(t):
        if "c" not in seen and int(dut.u_unit.g_bs.u_bs.bus_idle.value):
            seen["c"] = t.n
            t.drive(t.n, BUS, 0)
            t.drive(t.n + PERIOD, BUS, 1)
    toks = [ctrl("FRAME", 1 << 11 | len(f)), ctrl("SYNC"), line_op(stuff=True, crc_reset=True), *chunks(f[:-15]),
            line_op(stuff=True, crc_append=True), line_op(), (DATA, 2 << 12 | 0x7)]
    tb.send(*toks, at=tb.n + 1)
    tb.hook = other
    await tb.until_taken(len(toks))
    await tb.settle(PERIOD * 16)
    c = seen["c"]
    s = starts(tb)
    assert s == [c + 2], (s, c)                  # the other node's edge reaches the unit two clocks later (P1)
    s = s[0]
    assert tb.log[s]["aoe"] == 0 and tb.log[s + 1]["aoe"] == 1   # we drive our dominant first bit from edge s
    # the hard sync puts the bit start at the start of clock s: boundaries on edges s+20k, bits from s+1+20k
    assert bits_at(tb, s, len(line)) == line
    ours = [t for t, _ in tb.changes(BUS, s + 2) if t <= s + PERIOD * len(line)]
    assert ours and all((t - s - 1) % PERIOD == 0 for t in ours), (s, ours)
    assert got(tb) == [START] + expected_rx(f), got(tb)


@cocotb.test()
async def test_crc_reset_mid_frame_and_reset_before_append(dut):
    """P25: `LINE` [6] in mid-frame restarts the TX CRC, so it covers only the bits after it (a header outside the
    CRC, as in USB); within one `LINE` [6] acts before [3] (the register appended is CRC_INIT). A 5-bit CRC
    (poly 0x05, init 0x1F, CRC_XOR 0x0A), no stuffing, words with the length in the token."""
    if not FULL:
        return
    hdr, pay = 0x2D, 0x5A3

    def bits(v, n):
        return [(v >> (n - 1 - i)) & 1 for i in range(n)]
    c = crc_msb(bits(pay, 11), 0x05, 0x1F, 5) ^ 0x0A
    want = bits(hdr, 8) + bits(pay, 11) + bits(c, 5) + bits(0x1F ^ 0x0A, 5) + [0, 1, 0]
    tb = PinTb(dut)
    await tb.start(cfg(stuff_n=0, crc_width=5, crc_poly=0x05, crc_init=0x1F, crc_xor=0x0A), pads=0xFFFFFF)
    toks = [ctrl("SYNC"), (DATA, 7 << 12 | hdr), line_op(crc_reset=True), (DATA, 10 << 12 | pay),
            line_op(crc_append=True), line_op(crc_reset=True, crc_append=True), (DATA, 2 << 12 | 0b010)]
    tb.send(*toks, at=tb.n + 5)
    await tb.until_taken(len(toks))
    await tb.settle(PERIOD * 6)
    s = starts(tb)
    assert len(s) == 1, tb.loads
    assert bits_at(tb, s[0], len(want) + 2) == want + [1, 1]

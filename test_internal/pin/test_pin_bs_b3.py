"""L1-PIN, BITSYNC milestone B3 (§14 P24, P26-P29): readback and arbitration, bit errors, `JAM` responses and armed
error flags, listen-only, flag-delimited frames with aborts, NRZI, SE0, pin N, OE auto and data[14] "our own frame".

The references are code we did not write for this unit:
- `tools/protomodels/can.py`'s clock-level CANNode (Bosch CAN 2.0: bit timing, destuffing, CRC-15, ACK, error
  flags, arbitration) on the same wired-AND bus as the unit (pin A with OD = 1, IDLE = 1);
- `tools/protomodels/hdlc.py`'s encoder (ISO/IEC 13239 flags, zero insertion, FCS-16, aborts), driven on the line
  with a ±1 % clock error;
- `tools/protomodels/usb.py`'s line states (USB 2.0 low speed: NRZI, bit stuffing after six 1s, CRC-16, EOP =
  SE0 SE0 J), on D- (pin A / S) and D+ (pin N / B).

Expected values follow the §14 text. Where it leaves a choice the reading is named P-G<n> (D-055):
- P-G36 a response `JAM` is dropped if it is taken while a frame of ours is in progress;
- P-G37 ERR 0x2nnn (abort): nnn = the line bit of the abort in the frame, as ERR 0x1nnn;
- P-G38 `JAM` [0] without [4]: the bit is ignored, the JAM is a response;
- P-G39 readback applies to the bits from the TX queue (data, CRC, stuff, SE0, J), not to JAM bits;
- P-G40 a stuff error stops our TX only in a frame of ours;
- P-G41 status EVENTs wait in a one-entry register behind frame tokens (a second one is lost with OVERRUN).
Bit timing as in test_pin_bs_tx.py: our own frame starting at edge s has its bit k on the pad in clocks
s+1+PERIOD*k .. s+PERIOD*(k+1); a received frame starting (hard sync) in clock s0 has its bits on the same grid.
"""

import os

import cocotb

from pinlib import CTRL, DATA, ERR, EVENT, PAD, PinTb, ctrl, encode, enum, q8
from protomodels import can, hdlc, usb
from test_pin_bs_tx import (BS_RX, BS_TX, BUS, PERIOD, START, bits_at, can_frame_tokens, cfg, chunks,
                            expected_rx, got, starts)

FULL = int(os.environ.get("FULL", "0"))
JAM_ACK = ctrl("JAM", 0x000)            # dominant for 1 bit, from the next bit start
JAM_CRC = ctrl("JAM", 0x580)            # dominant for 6 bits, after 3 more non-stuff sample points
JAM_ARM = ctrl("JAM", 0x510)            # armed: 6 dominant bits from the bit after the next error
JAM_DISARM = ctrl("JAM", 0x011)
TX_OFF = ctrl("JAM", 0x002)
TX_ON = ctrl("JAM", 0x004)
REFUSED = (EVENT, 0xC001)


def line(stuff=False, crc_reset=False, crc_append=False, rb=0, se0=0):
    return ctrl("LINE", (se0 - 1 if se0 else 0) << 8 | crc_reset << 6 | bool(se0) << 4 | crc_append << 3
                | stuff << 2 | rb)


def can_tx(f, arb=1, rest=3, ack=2):
    """A CAN frame as the CAN program sends it: arbitration readback over the header and data, then strict,
    the CRC, the CRC delimiter, the ACK slot (expect an override), the ACK delimiter and EOF."""
    return [ctrl("FRAME", 1 << 11 | len(f)), ctrl("SYNC"), line(stuff=True, crc_reset=True, rb=arb),
            *chunks(f[:-15]), line(stuff=True, crc_append=True, rb=rest), line(rb=rest), (DATA, 1),
            line(rb=ack), (DATA, 1), line(rb=rest), (DATA, 7 << 12 | 0xFF), line()]


def rb_event(kind, lvl, bit):
    return (EVENT, {1: 0x8000, 2: 0xA000, 3: 0xB000}[kind] | lvl << 14 | bit << 1)


class Bus:
    """Per clock: the wired-AND of a scripted level, a reference CAN node and forced-low windows, plus a record
    of the engine's state (white-box probes)."""

    def __init__(self, dut, node=None):
        self.dut, self.node = dut, node
        self.script = None                    # f(clock) -> level
        self.low = set()                      # clocks the bus is forced dominant
        self.rec = {}                         # clock -> (jbit and drv, in_frame, bus_idle)
        self.on_clock = []                    # f(tb) callbacks

    def __call__(self, tb):
        bs = self.dut.u_unit.g_bs.u_bs
        self.rec[tb.n] = (int(bs.jbit.value) & int(bs.drv.value), int(bs.in_frame.value), int(bs.bus_idle.value))
        for f in list(self.on_clock):
            f(tb)
        v = 0 if tb.n in self.low else 1
        if self.script is not None:
            v &= self.script(tb.n)
        if self.node is not None:
            bus = tb.log[-1]["line"] >> BUS & 1 if tb.log else 1
            v &= self.node.step(bus)
        tb.drive(tb.n, BUS, v)

    def jam_bits(self, lo, hi):
        return [n for n in range(lo, hi) if self.rec.get(n, (0,))[0]]

    def first_idle(self, since):
        return next(n for n in sorted(self.rec) if n >= since and self.rec[n][2])

    def frame_start(self, since):
        """The clock of the next frame start (in_frame rises on the edge after it)."""
        return next(n for n in sorted(self.rec) if n > since and self.rec[n][1] and not self.rec[n - 1][1]) - 1


async def until_loads(tb, count, limit=40000):
    t0 = tb.n
    while len(tb.loads) < count:
        assert tb.n - t0 < limit, (count, tb.loads)
        await tb.settle()


def when_idle(bus, dut, action):
    """Run action(tb) once, in the first clock the engine's bus is idle."""
    def f(tb):
        if int(dut.u_unit.g_bs.u_bs.bus_idle.value):
            bus.on_clock.remove(f)
            action(tb)
    bus.on_clock.append(f)


@cocotb.test()
async def test_arbitration_lost_discard_and_sync_rearm(dut):
    """P26 mode 1: we and another node start together (we join its first bit, P21); our ID is higher, so at the
    first ID bit where we send recessive and read dominant we emit EVENT 0x8000 | bit << 1 (level 0), clear the TX
    queue and discard the rest of our DATA/LINE tokens. We then only receive: the other frame's words and a
    verdict without data[14] (not our own frame). The bit we lose on completes the first word, so the word and the
    status EVENT want the same clock: the word goes first and the EVENT follows (P-G41). The reference node
    decodes and ACKs the winner. A SYNC re-arms:
    our next frame goes out after bus idle and the reference node decodes it."""
    if not FULL:
        return
    fw, fo = can.frame_fields(0x100, [0x11]), can.frame_fields(0x110, [0x22])
    lw, lo = can.stuff(fw) + [1] * 10, can.stuff(fo)
    lost = next(i for i in range(len(lo)) if lo[i] == 1 and lw[i] == 0)
    assert lo[:lost] == lw[:lost] and lost == 7          # bit 7 ends the first 8-bit word
    node = can.CANNode(PERIOD, sp=0.75)
    bus = Bus(dut, node)
    tb = PinTb(dut)
    await tb.start(cfg(), pads=0xFFFFFF)
    tb.hook = bus
    st = {}

    def winner(tb):
        st["c"] = tb.n
        bus.script = lambda n: lw[(n - st["c"]) // PERIOD] if (n - st["c"]) // PERIOD < len(lw) else 1
    when_idle(bus, dut, winner)
    toks = [ctrl("FRAME", 1 << 11 | len(fw)), ctrl("SYNC"), line(stuff=True, crc_reset=True, rb=1),
            *chunks(fo[:-15]), line(stuff=True, crc_append=True, rb=1), line(), (DATA, 9 << 12 | 0x3FF)]
    tb.send(*toks, at=tb.n + 1)
    await tb.until_taken(len(toks))
    while not node.received and tb.n < 20000:
        await tb.settle(50)
    s = st["c"] + 2
    assert starts(tb) == [s], (starts(tb), st)
    assert [(r["id"], r["crc_ok"]) for r in node.received] == [(0x100, True)]
    rx = expected_rx(fw, own=False)
    assert got(tb) == [START, rx[0], rb_event(1, 0, lost)] + rx[1:], got(tb)
    after = s + 1 + PERIOD * (lost + 1)
    assert all(tb.log[n]["aoe"] == 0 for n in range(after, s + PERIOD * len(lw))), "we drove after losing"

    f2 = can.frame_fields(0x155, [0x44, 0x45])
    k = len(tb.takes)
    tb.send(*can_frame_tokens(f2), at=tb.n + 1)
    await tb.until_taken(k + len(can_frame_tokens(f2)))
    while len(node.received) < 2 and tb.n < 40000:
        await tb.settle(50)
    assert [(r["id"], r["data"], r["crc_ok"]) for r in node.received[1:]] == [(0x155, [0x44, 0x45], True)]
    assert got(tb)[-len(expected_rx(f2)) - 1:] == [START] + expected_rx(f2)
    assert tb.log[-1]["ovr"] == 0


@cocotb.test()
async def test_ack_slot_errors_armed_jam_and_discard(dut):
    """P26 mode 2 in the ACK slot: with the reference node ACKing, EVENT 0xA000 | bit << 1 (the dominant ACK), no
    error, and a response JAM taken during our own frame is dropped (P28). Then JAM armed and disarmed: without an
    ACK the slot reads recessive, EVENT 0xE000 | bit << 1, an error, but no flag. Armed again, the same frame's
    error fires 6 dominant bits from the next bit start (the ACK delimiter) and the rest of our frame's tokens
    are discarded; a DATA token is still discarded until `WAIT` [1], after which the next one goes out. Mode 3: a
    recessive bit of ours read dominant is a bit error, EVENT 0xB000 | bit << 1, and the armed flag follows."""
    if not FULL:
        return
    node = can.CANNode(PERIOD, sp=0.75)
    bus = Bus(dut, node)
    tb = PinTb(dut)
    await tb.start(cfg(), pads=0xFFFFFF)
    tb.hook = bus

    # (a) ACKed; a response JAM during our own frame is dropped
    f = can.frame_fields(0x321, [0x5A, 0xC3])
    L = len(can.stuff(f))
    toks = can_tx(f) + [JAM_ACK]
    tb.send(*toks, at=tb.n + 1)
    await tb.until_taken(len(toks))
    await tb.settle(PERIOD * 14)
    s = starts(tb)[0]
    assert [(r["id"], r["crc_ok"]) for r in node.received] == [(0x321, True)]
    assert got(tb) == [START] + expected_rx(f) + [rb_event(2, 0, L + 1)], got(tb)
    assert bits_at(tb, s, L + 3) == can.stuff(f) + [1, 0, 1]
    assert bus.jam_bits(s, tb.n) == [], "the JAM in our own frame was not dropped"

    # (b) no ACK: armed then disarmed -> no flag
    node.ack = False
    n0 = len(tb.loads)
    f = can.frame_fields(0x2F0, [0x01])
    L = len(can.stuff(f))
    toks = [JAM_ARM, JAM_DISARM] + can_tx(f)
    k = len(tb.takes)
    tb.send(*toks, at=tb.n + 1)
    await tb.until_taken(k + len(toks))
    await tb.settle(PERIOD * 14)
    s = starts(tb)[-1]
    assert got(tb)[n0:] == [START] + expected_rx(f) + [rb_event(2, 1, L + 1)], got(tb)[n0:]
    assert bus.jam_bits(s, tb.n) == []

    # (c) armed: the error fires 6 dominant bits at the ACK delimiter; the rest is discarded
    n0 = len(tb.loads)
    toks = [JAM_ARM] + can_tx(f)
    k = len(tb.takes)
    tb.send(*toks, at=tb.n + 1)
    await tb.until_taken(k + len(toks))
    await tb.settle(PERIOD * 14)
    s = starts(tb)[-1]
    assert got(tb)[n0:n0 + len(expected_rx(f)) + 2] == [START] + expected_rx(f) + [rb_event(2, 1, L + 1)]
    # our 6 dominant bits from the ACK delimiter; the reference node answers the ACK delimiter's form error
    # with its own flag one bit later, so the bus is dominant for 7 bits
    assert bits_at(tb, s, L + 8) == can.stuff(f) + [1, 1] + [0] * 6
    jam = bus.jam_bits(s, tb.n)
    assert jam == list(range(s + 1 + PERIOD * (L + 2), s + 1 + PERIOD * (L + 8))), (jam[:3], jam[-3:], s, L)

    # discarded until WAIT [1]
    await tb.settle(PERIOD * 14)
    k = len(tb.takes)
    t0 = tb.n
    tb.send((DATA, 3 << 12 | 0b0000), at=t0 + 1)
    await tb.until_taken(k + 1)
    await tb.settle(PERIOD * 6)
    assert all(r["aoe"] == 0 for r in tb.log[t0:]), "a discarded DATA token was sent"
    tb.send(ctrl("WAIT", 2), (DATA, 3 << 12 | 0b0101), at=tb.n + 1)
    await tb.until_taken(k + 3)
    t1 = tb.takes[-1][0]
    await tb.settle(PERIOD * 6)
    assert any(r["aoe"] for r in tb.log[t1:]), "after WAIT [1] the DATA token did not go out"

    # (d) mode 3 bit error on a recessive bit of ours, armed flag after it
    node.ack = True
    await tb.settle(PERIOD * 14)
    f = can.frame_fields(0x0F1, [0xF0, 0x0F])
    lf = can.stuff(f)
    kb = next(i for i in range(20, len(lf) - 16) if lf[i] == 1)
    n0 = len(tb.loads)
    st = {}

    def force(tb):
        if "s" not in st and len(tb.loads) > n0 and tb.loads[n0][1:] == START:
            st["s"] = tb.loads[n0][0]
            bus.low.update(range(st["s"] + 1 + PERIOD * kb, st["s"] + 1 + PERIOD * (kb + 1)))
    bus.on_clock.append(force)
    toks = [JAM_ARM] + can_tx(f, arb=3)
    k = len(tb.takes)
    tb.send(*toks, at=tb.n + 1)
    await tb.until_taken(k + len(toks))
    await tb.settle(PERIOD * 20)
    s = st["s"]
    assert rb_event(3, 0, kb) in got(tb)[n0:], (kb, got(tb)[n0:])
    jam = bus.jam_bits(s, tb.n)
    assert jam == list(range(s + 1 + PERIOD * (kb + 1), s + 1 + PERIOD * (kb + 7))), (jam[:2], jam[-2:], s, kb)
    assert all(tb.log[n]["aoe"] == 0 for n in range(s + 1 + PERIOD * (kb + 7), tb.n)), "we sent after the error"


@cocotb.test()
async def test_jam_responses_in_another_nodes_frame(dut):
    """P28, not armed: the reference node sends; after our verdict EVENT a JAM (n 1, d 0) drives the ACK slot
    exactly (the first bit start after one more non-stuff sample point: the CRC delimiter, not the stuff bit
    after this frame's CRC); the node counts its
    frame as ACKed. After a CRC error (the node flips its last CRC bit), JAM (n 6, d 2) drives the 6 bits after the ACK delimiter. A new response
    replaces a pending one."""
    if not FULL:
        return
    node = can.CANNode(PERIOD, sp=0.75, retries=0)
    bus = Bus(dut, node)
    tb = PinTb(dut)
    await tb.start(cfg(), pads=0xFFFFFF)
    tb.hook = bus
    post = next((cid, [d]) for cid in range(0x200, 0x7FF, 7) for d in range(0, 256, 17)
                if len(set(can.frame_fields(cid, [d])[-5:])) == 1
                and len(set(can.stuff(can.frame_fields(cid, [d]))[-6:-1])) == 1)
    cases = [(post[0], post[1], False, [JAM_ACK], (1, 2)),
             (0x3B6, [0x44, 0x55], True, [JAM_CRC], (3, 9)),
             (0x1C7, [0x66], False, [JAM_ACK, ctrl("JAM", 0x140)], (2, 4))]
    for cid, data, bad, jams, (b0, b1) in cases:
        f = can.frame_fields(cid, data)
        L = len(can.stuff(f))
        n0 = len(tb.loads)
        k = len(tb.takes)
        tb.send(ctrl("FRAME", 1 << 11 | len(f)), at=tb.n + 1)
        await tb.until_taken(k + 1)
        await tb.settle(PERIOD * 14)
        t0 = tb.n
        node.corrupt_crc = bad
        when_idle(bus, dut, lambda tb, cid=cid, data=data: node.queue(cid, data))
        sent = f[:-1] + [f[-1] ^ 1] if bad else f          # the node flips its last CRC bit
        want = expected_rx(sent, crc_good=not bad, own=False)
        await until_loads(tb, n0 + len(want))
        tb.send(*jams, at=tb.n + 3)
        await tb.until_taken(k + 1 + len(jams))
        await tb.settle(PERIOD * 24)
        assert got(tb)[n0:] == want, (cid, got(tb)[n0:])
        s0 = bus.frame_start(t0)
        jam = bus.jam_bits(t0, tb.n)
        assert jam == list(range(s0 + 1 + PERIOD * (L + b0), s0 + 1 + PERIOD * (L + b1))), \
            (cid, jam[:2], jam[-2:], s0, L)
        await tb.settle(PERIOD * 30)
    assert node.results[0] == (post[0], "acked"), node.results
    assert [(r["id"], r["crc_ok"]) for r in node.received] == [], node.received


@cocotb.test()
async def test_listen_only(dut):
    """P28 [1]/[2] ([1] and [2] together: [1] wins): in listen-only nothing is driven: a SYNC is refused with EVENT 0xC001, the frame's DATA and LINE
    tokens are discarded, a response JAM is ignored; frames are still received. After [2] (TX on) a SYNC frame
    goes out and the reference node decodes it."""
    if not FULL:
        return
    node = can.CANNode(PERIOD, sp=0.75, retries=0)
    bus = Bus(dut, node)
    tb = PinTb(dut)
    await tb.start(cfg(), pads=0xFFFFFF)
    tb.hook = bus
    f = can.frame_fields(0x111, [0x22])
    toks = [ctrl("JAM", 0x006)] + can_frame_tokens(f)               # [1] with [2]: [1] wins
    tb.send(*toks, at=tb.n + 1)
    await tb.until_taken(len(toks))
    await tb.settle(PERIOD * 30)
    assert got(tb) == [REFUSED], got(tb)
    g = can.frame_fields(0x444, [0x55])
    when_idle(bus, dut, lambda tb: node.queue(0x444, [0x55]))
    k = len(tb.takes)
    tb.send(ctrl("FRAME", 1 << 11 | len(g)), at=tb.n + 1)
    await until_loads(tb, 1 + len(expected_rx(g)))
    tb.send(JAM_ACK, at=tb.n + 3)
    await tb.until_taken(k + 2)
    await tb.settle(PERIOD * 40)
    assert got(tb)[1:1 + len(expected_rx(g))] == expected_rx(g, own=False)
    assert all(r["aoe"] == 0 for r in tb.log), "something was driven in listen-only"
    assert bus.jam_bits(0, tb.n) == []
    await tb.settle(PERIOD * 30)
    k = len(tb.takes)
    toks = [TX_ON] + can_frame_tokens(f)
    tb.send(*toks, at=tb.n + 1)
    await tb.until_taken(k + len(toks))
    while not node.received and tb.n < 30000:
        await tb.settle(50)
    assert [(r["id"], r["crc_ok"]) for r in node.received] == [(0x111, True)]
    assert len(starts(tb)) == 1
    await tb.settle(PERIOD * 30)
    k, n0 = len(tb.takes), len(tb.loads)
    tb.send(TX_OFF, ctrl("SYNC"), at=tb.n + 1)                      # [1] alone
    await tb.until_taken(k + 2)
    await tb.settle(PERIOD * 4)
    assert got(tb)[n0:] == [REFUSED], got(tb)[n0:]


def flag_expect(frames, bad=(), abort=None):
    """RX tokens for hdlc.encode(frames, ...) under P27: every byte of a good or bad frame (FCS included) as DATA,
    then EVENT / ERR with the empty last word; an aborted frame: the bytes committed before the abort (a bit is
    committed when STUFF_N + 1 = 6 newer destuffed bits have arrived; the 6th and 7th 1 are not destuffed bits),
    then ERR 0x2nnn with nnn = the abort's line bit after the opening flag."""
    out = []
    for i, data in enumerate(frames):
        if abort and abort[0] == i:
            body = hdlc.bits_of(data[:abort[1]])
            ones = 0
            for b in reversed(body):
                if not b:
                    break
                ones += 1
            destuffed = body + [1] * (5 - ones)
            committed = destuffed[:len(destuffed) - 6]
            out += [(DATA, sum(committed[8 * k + j] << j for j in range(8))) for k in range(len(committed) // 8)]
            line = hdlc.stuff(body)
            run, n = ones, len(line)
            while run < 7:
                run, n = run + 1, n + 1
            out.append((ERR, 0x2000 | (n - 1)))
            continue
        fcs = hdlc.fcs16(data) ^ 0xFFFF ^ (0x0100 if i in bad else 0)
        out += [(DATA, b) for b in list(data) + [fcs & 0xFF, fcs >> 8]]
        out.append((ERR, 0) if i in bad else (EVENT, 0))
    return out


@cocotb.test()
async def test_flag_delimited_rx_with_drift(dut):
    """P27 (DELIM = flag, HDLC): frames from protomodels.hdlc at +1 % and then -1 % bit rate, with two flags and
    then one shared flag between frames. Opening flags report nothing; each frame gives its bytes (FCS included)
    and EVENT 0x000 on a good FCS (residue 0x1D0F), ERR 0x0000 on a bad one; an abort (seven 1s) gives ERR 0x2nnn
    after the committed bytes; the idle after it ends nothing."""
    if not FULL:
        return
    fa = [[0x12, 0x7E, 0xFF, 0x00], [0x34, 0x56], [0xA5, 0x3C, 0x99], [0xF0, 0x0F, 0x55]]
    fb = [[0xFF, 0xFF], [0x81, 0x7E, 0x3F]]
    la = hdlc.encode(fa, flags_between=2, bad_fcs=(1,), abort_after=(2, 2))
    lb = hdlc.encode(fb, flags_between=1)
    tb = PinTb(dut)
    await tb.start(cfg(order=0, tx_lentok=0, nbits=7, rx_nbits=8, stuff_lvl=enum("stuff_lvl", 1), crc_width=16,
                       crc_poly=0x1021, crc_init=0xFFFF, crc_xor=0xFFFF, crc_res=0x1D0F, idle_bits=8,
                       sampleofs=q8(10), sjw=q8(5), delim=enum("delim", "flag")), pads=0xFFFFFF)
    t = tb.n + 10
    tb.drive_bits(t, BUS, la, PERIOD * 1.01)
    t += int(len(la) * PERIOD * 1.01) + 5
    tb.drive_bits(t, BUS, lb, PERIOD * 0.99)
    await tb.until(t + int(len(lb) * PERIOD * 0.99) + 40)
    want = flag_expect(fa, bad=(1,), abort=(2, 2)) + flag_expect(fb)
    assert got(tb) == want, (got(tb), want)
    assert tb.log[-1]["ovr"] == 0 and all(r["aoe"] == 0 for r in tb.log)


DM, DP = PAD["uio0"], PAD["uio1"]
J_PADS = 0xFFFFFF & ~(1 << DP)                    # the idle state J: D- high, D+ low


def usb_cfg():
    return encode(txmode=BS_TX, rxmode=BS_RX, pin_a=DM, pin_n=DP, pin_s=DM, pin_b=DP, od=0, idle=1, order=0,
                  tx_lentok=0, nbits=7, rx_nbits=8, period=q8(PERIOD), sampleofs=q8(10), sjw=q8(5),
                  resync=enum("resync", "both"), idle_bits=2, stuff_n=6, stuff_lvl=enum("stuff_lvl", 1),
                  crc_width=16, crc_poly=0x8005, crc_init=0xFFFF, crc_xor=0xFFFF, crc_res=0x800D, crc_skip=16,
                  nrzi=1, oe_auto=1, delim=enum("delim", "se0"))


@cocotb.test()
async def test_nrzi_se0_pin_n_oe_auto_tx(dut):
    """P29 TX (USB low speed): SYNC, LINE (stuffing), the SYNC byte and PID, LINE (CRC reset), the payload, LINE
    (append the CRC-16), LINE [4] (SE0 for 2 bits). On D- (pin A) and D+ (pin N) every bit equals
    protomodels.usb's line states for the same packet: NRZI, a stuffed 0 after six 1s, the CRC-16, SE0 SE0 (both
    low), J; then the pads are released. With OE_AUTO they are driven only from our first bit to the J bit, and our
    own packet is not reported (only EVENT 0x9001)."""
    if not FULL:
        return
    payload = [0xFF, 0xFF, 0x00, 0x7F, 0xC3]
    states = usb.line_states(usb.data_packet(usb.DATA1, payload))
    tb = PinTb(dut)
    await tb.start(usb_cfg(), pads=J_PADS)
    toks = [ctrl("SYNC"), line(stuff=True), (DATA, 0x80), (DATA, usb.DATA1), line(stuff=True, crc_reset=True),
            *[(DATA, b) for b in payload], line(stuff=True, crc_append=True), line(se0=2)]
    tb.send(*toks, at=tb.n + 1)
    await tb.until_taken(len(toks))
    await until_loads(tb, 1)
    s = starts(tb)[0]
    await tb.until(s + PERIOD * (len(states) + 4))
    assert got(tb) == [START], got(tb)
    seen = [(tb.line(DP, s + 1 + PERIOD * i + PERIOD // 2), tb.line(DM, s + 1 + PERIOD * i + PERIOD // 2))
            for i in range(len(states))]
    assert seen == states, (seen, states)
    end = s + PERIOD * len(states)
    assert all(tb.log[n]["aoe"] == tb.log[n]["noe"] == int(s < n <= end) for n in range(s - 20, end + 60))
    assert all(tb.line(DM, n) == 1 and tb.line(DP, n) == 0 for n in range(end + 1, end + 60))


@cocotb.test()
async def test_nrzi_se0_rx(dut):
    """P29 RX (USB low speed, DELIM = se0, IDLE_BITS 2): packets from protomodels.usb on D- (pin S) and D+ (pin B)
    at +0.5 % bit rate. NRZI and destuffing give the bytes (SYNC and PID included); long runs without a transition
    do not end the packet (idle never ends a frame with DELIM = se0); SE0 ends it with the verdict on the CRC-16
    after CRC_SKIP = 16 bits: EVENT 0x000 for a good data packet, ERR 0x000 for a bad one and for a token (no
    CRC-16)."""
    if not FULL:
        return
    pkts = [(usb.data_packet(usb.DATA0, [0xFF, 0xFF, 0x80, 0x00, 0x3E]), True),
            (usb.data_packet(usb.DATA1, [0x12, 0x34], bad_crc=True), False),
            (usb.token(usb.IN, 5, 0), False),
            (usb.data_packet(usb.DATA1, []), True)]
    tb = PinTb(dut)
    await tb.start(usb_cfg(), pads=J_PADS)
    t = tb.n + PERIOD * 4                              # the bus is idle after IDLE_BITS samples
    want = []
    for pkt, good in pkts:
        for i, (dp, dm) in enumerate(usb.line_states(pkt)):
            c = t + int(i * PERIOD * 1.005)
            tb.drive(c, DP, dp)
            tb.drive(c, DM, dm)
        t += int(len(usb.line_states(pkt)) * PERIOD * 1.005)
        tb.drive(t, DP, 0)
        tb.drive(t, DM, 1)
        t += PERIOD * 8
        want += [(DATA, b) for b in pkt] + [(EVENT, 0) if good else (ERR, 0)]
    await tb.until(t + 20)
    assert got(tb) == want, (got(tb), want)
    assert tb.log[-1]["ovr"] == 0 and all(r["aoe"] == 0 and r["noe"] == 0 for r in tb.log)

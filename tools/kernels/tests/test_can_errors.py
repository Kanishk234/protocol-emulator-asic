"""L3-CAN part 2 on the model: 29-bit IDs, remote frames, error flags and error counters
(programs/can.trw) against the reference CAN 2.0 node and sigrok."""

import re
import shutil
import subprocess

from protomodels.can import crc15, frame_line_bits
from test_can import Bus, frame_clocks, make, send, sigrok_frames
from tripsim.isa import TAG_DATA, TAG_ERR, TAG_EVENT

PERIOD = 100                                     # 500 kbit/s
TR = 12 * PERIOD


def host_frames(got):
    """Host-side decode of 29/11-bit frames: [(id, ext, rtr, dlc, data, ok)]."""
    out, words = [], []
    for tag, d in got:
        if tag == TAG_DATA:
            words.append(d)
        elif tag == TAG_EVENT and not d & 0x8000 or tag == TAG_ERR and not d & 0x8000 and d >> 12 == 0:
            bits = "".join(f"{w:012b}" for w in words)
            ext = bits[13] == "1"
            head = 39 if ext else 19
            rtr = int(bits[32] if ext else bits[12])
            dlc = int(bits[head - 4:head], 2)
            n = head + (0 if rtr else 8 * min(dlc, 8)) + 15
            bits += f"{d & 0xFFF:0{n - len(bits)}b}" if n > len(bits) else ""
            cid = int(bits[1:12] + bits[14:32], 2) if ext else int(bits[1:12], 2)
            data = [] if rtr else [int(bits[head + 8 * k:head + 8 + 8 * k], 2) for k in range(min(dlc, 8))]
            ok = tag == TAG_EVENT and crc15([int(b) for b in bits[:-15]]) == int(bits[-15:], 2)
            out.append((cid, ext, bool(rtr), dlc, data, ok))
            words = []
        elif tag == TAG_ERR and not d & 0x8000:
            words = []
    return out


def ref_frames(node):
    return [(r["id"], r["ext"], r["rtr"], r["dlc"], r["data"]) for r in node.received]


def test_extended_and_remote_frames_both_ways(tmp_path):
    from protomodels.can import CANNode
    chip = make(PERIOD)
    ref = CANNode(PERIOD)
    bus = Bus(chip, [ref], vcd=True)
    bus.run(TR)
    send(chip, 0x1ABCDE12, [0x11, 0x22, 0x33], ext=True)          # ours: 29-bit data frame
    send(chip, 0x0000_0FFF, ext=True, rtr=True, dlc=0)            # 29-bit remote frame (DLC 0: see below)
    send(chip, 0x123, rtr=True, dlc=0)                            # 11-bit remote frame
    bus.run(3 * frame_clocks(PERIOD, 8) + 20 * PERIOD)
    assert ref_frames(ref) == [(0x1ABCDE12, True, False, 3, [0x11, 0x22, 0x33]),
                               (0xFFF, True, True, 0, []), (0x123, False, True, 0, [])]
    ref.queue(0x18FF1234, [0xDE, 0xAD], ext=True)                  # theirs: 29-bit data frame
    ref.queue(0x7F0, rtr=True, dlc=0)                              # 11-bit remote frame
    ref.queue(0x0155555, rtr=True, dlc=0, ext=True)
    bus.run(3 * frame_clocks(PERIOD, 2) + 20 * PERIOD)
    got = [f for f in host_frames(bus.got)]
    assert [f[:5] for f in got] == [(0x1ABCDE12, True, False, 3, [0x11, 0x22, 0x33]),
                                    (0xFFF, True, True, 0, []), (0x123, False, True, 0, []),
                                    (0x18FF1234, True, False, 2, [0xDE, 0xAD]),
                                    (0x7F0, False, True, 0, []), (0x0155555, True, True, 0, [])]
    assert all(f[5] for f in got)
    assert [r for r in ref.results] == [(0x18FF1234, "acked"), (0x7F0, "acked"), (0x0155555, "acked")]
    # this sigrok version treats a remote frame with DLC > 0 (11- or 29-bit) as if it had data:
    # it reads the ACK slot in the wrong place and loses sync, so the frames above use DLC 0; the
    # reference node checks remote frames with a DLC in the next test
    if shutil.which("sigrok-cli"):
        bus.rec.write(tmp_path / "can.vcd")
        out = sigrok_frames(tmp_path / "can.vcd", PERIOD)
        full = [int(x, 16) for x in re.findall(r"Full Identifier: \d+ \(0x([0-9a-f]+)\)", out)]
        assert full == [0x1ABCDE12, 0xFFF, 0x18FF1234, 0x0155555], out
        assert out.count("Remote transmission request: remote frame") == 4, out
        assert out.count("ACK slot: ACK") == 6 and "error" not in out.lower(), out


def test_remote_frames_with_a_dlc():
    """A remote frame has no data field whatever its DLC (11- and 29-bit IDs)."""
    from protomodels.can import CANNode
    chip = make(PERIOD)
    ref = CANNode(PERIOD)
    bus = Bus(chip, [ref])
    bus.run(TR)
    send(chip, 0x0ABCDEF, ext=True, rtr=True, dlc=4)
    send(chip, 0x123, rtr=True, dlc=8)
    ref.queue(0x3FFFFFF, rtr=True, dlc=8, ext=True)                # all ones: heavy stuffing
    ref.queue(0x7F0, rtr=True, dlc=2)
    bus.run(4 * frame_clocks(PERIOD, 0) + 40 * PERIOD)
    assert sorted(ref_frames(ref)) == [(0x123, False, True, 8, []), (0x0ABCDEF, True, True, 4, [])]
    assert all(r["crc_ok"] for r in ref.received)
    assert sorted(host_frames(bus.got)) == [(0x123, False, True, 8, [], True),
                                            (0x7F0, False, True, 2, [], True),
                                            (0x0ABCDEF, True, True, 4, [], True),
                                            (0x3FFFFFF, True, True, 8, [], True)]
    assert sorted(r for r in ref.results if r[1] == "acked") == [(0x7F0, "acked"), (0x3FFFFFF, "acked")]
    assert all(r[1] in ("acked", "lost") for r in ref.results)     # it may lose arbitration to us


def test_crc_error_gets_an_error_flag_and_a_retransmission():
    from protomodels.can import CANNode
    chip = make(PERIOD)
    ref = CANNode(PERIOD, corrupt_crc=True)                        # the first attempt only
    bus = Bus(chip, [ref])
    bus.run(TR)
    ref.queue(0x321, [9, 8, 7])
    bus.run(2 * frame_clocks(PERIOD, 3) + 30 * PERIOD)
    errs = [d for t, d in bus.got if t == TAG_ERR and not d & 0x8000]
    assert len(errs) == 1 and errs[0] >> 12 == 0                   # we saw the CRC error ...
    # the transmitter sees no ACK first (we never ACK a bad CRC) and flags an ACK error; our CRC
    # error flag follows the ACK delimiter
    assert ref.errors and ref.errors[0][0] == "ack"
    assert ref.results == [(0x321, "noack"), (0x321, "acked")]     # it retried, we took the retry
    assert [f[:5] for f in host_frames(bus.got) if f[5]] == [(0x321, False, False, 3, [9, 8, 7])]


class Glitch(Bus):
    """A bus with a disturber that forces the line dominant for one bit at a chosen line bit
    of every frame our chip starts (bit counted from our SOF)."""

    def __init__(self, chip, nodes, bit, frames=1):
        super().__init__(chip, nodes)
        self.bit, self.frames, self.sof, self.t, self.quiet = bit, frames, None, 0, 0
        self.txd = []                                            # our TXD, every clock

    def run(self, clocks):
        for _ in range(int(clocks)):
            ours = self.chip.outputs()[0] & 1
            self.txd.append(ours)
            if (self.sof is None and ours == 0 and self.level == 1 and self.frames
                    and self.quiet >= 11 * PERIOD):                # a real SOF, not an error flag
                self.sof = self.t
            self.quiet = self.quiet + 1 if self.level == 1 else 0
            forced = self.sof is not None and 0 <= self.t - self.sof - self.bit * PERIOD < PERIOD
            if self.sof is not None and self.t - self.sof >= (self.bit + 1) * PERIOD:
                self.sof, self.frames = None, self.frames - 1
            self.level = ours
            for n in self.nodes:
                self.level &= n.drive
            if forced:
                self.level = 0
            self.hist.append(self.level)
            self.chip.ui_in = self.hist.pop(0)
            self.chip.step()
            for n in self.nodes:
                n.step(self.level)
            while self.chip.host_out:
                self.got.append(self.chip.host_out.popleft())
            self.t += 1


def first_recessive_after(bits, start):
    return next(i for i in range(start, len(bits)) if bits[i] == 1)


def test_bit_error_in_our_frame_error_flag_and_counters():
    from protomodels.can import CANNode
    data = [0xF0, 0xF0]
    line = frame_line_bits(0x456, data)
    hit = first_recessive_after(line, 21)                          # a recessive data bit of ours
    chip = make(PERIOD)
    ref = CANNode(PERIOD)
    bus = Glitch(chip, [ref], bit=hit, frames=1)
    bus.run(TR)
    send(chip, 0x456, data)
    bus.run(frame_clocks(PERIOD, 2) + 30 * PERIOD)
    results = [d for t, d in bus.got if t == TAG_EVENT and d & 0x8000 and d not in (0x9001, 0xC001)]
    assert len(results) == 1 and results[0] & 0xB000 == 0xB000      # a bit error (0xB000/0xF000)
    assert ref.errors and ref.errors[0][0] == "stuff"              # our error flag reached it
    runs, n = [], 0
    for v in bus.txd:
        n = n + 1 if v == 0 else 0
        runs.append(n)
    assert max(runs) >= 6 * PERIOD - 10                            # we drove the 6-bit error flag
    assert ref.received == []
    send(chip, 0x456, data)                                        # the host retries: clean now
    bus.run(frame_clocks(PERIOD, 2) + 30 * PERIOD)
    assert [(r["id"], r["data"]) for r in ref.received] == [(0x456, data)]


def test_passive_then_bus_off_then_recovery():
    from protomodels.can import CANNode
    data = [0xF0]
    hit = first_recessive_after(frame_line_bits(0x100, data), 21)
    chip = make(PERIOD)
    ref = CANNode(PERIOD)
    bus = Glitch(chip, [ref], bit=hit, frames=40)
    bus.run(TR)
    states = lambda: [d & 3 for t, d in bus.got if t == TAG_ERR and d & 0x8000]
    for attempt in range(33):                                      # every attempt hits a bit error
        send(chip, 0x100, data)
        bus.run(frame_clocks(PERIOD, 1) + 30 * PERIOD)
        if states()[-1] == 2:
            break
    assert states() == [0, 1, 2] and attempt == 31                 # TEC 128 -> passive, 256 -> bus-off
    send(chip, 0x100, data)                                        # bus-off: refused, nothing sent
    mark = len(bus.txd)
    bus.run(frame_clocks(PERIOD, 1))
    assert [d for t, d in bus.got if t == TAG_EVENT][-1] == 0xC001
    assert all(bus.txd[mark:])                                     # listen-only: TXD stays recessive
    ref.queue(0x2AA, [1, 2])                                       # another node's frame: a bus-off
    bus.run(2 * frame_clocks(PERIOD, 2))                           # node does not even ACK it
    assert all(bus.txd[mark:]) and (0x2AA, "noack") in ref.results
    ref.pending.clear()
    bus.frames = 0
    chip.host_push(0, tag=0x1)                                     # CTRL: recover
    bus.run(4 * PERIOD)
    send(chip, 0x100, data)
    bus.run(frame_clocks(PERIOD, 1) + 30 * PERIOD)
    assert states()[-1] == 0
    assert [(r["id"], r["data"]) for r in ref.received] == [(0x100, data)]

"""TRIPWIRE host library: §9 transactions, the D-046 register map, and image loading (§14 H1).

Addresses and layouts come from tools/tripwire_spec.py (generated from spec/tripwire.yaml `host_map`).
"""

import tripwire_spec as S

HM = {name: addr for name, (addr, _) in S.HOST_MAP.items()}
LW = {w: j for j, w in enumerate(S.HOST_LANE_WORDS)}
UNITS = len(S.PIN_UNIT_FEATURES)
LANES = S.HOST_MAP["lanes"][1] // S.HOST_LANE_STRIDE
PC_WORDS = max((bit + width - 1) // 16 for bit, width, _ in S.PIN_CFG_FIELDS.values()) + 1
HOST_PADS = set(S.HOST_PADS)
WRITE = 0x80


# ----------------------------------------------------------------------------- transactions (§9)
def frame_write(addr, words):
    """Bytes of a write transaction: CMD (bit 7 = 1), ADDR[15:0], 16-bit words MSB first."""
    out = [WRITE, addr >> 8 & 0xFF, addr & 0xFF]
    for w in words:
        out += [w >> 8 & 0xFF, w & 0xFF]
    return bytes(out)


def frame_read(addr, n):
    """(bytes to send, parse): a read of n words; the reply has one dummy byte after the address."""
    out = bytes([0x00, addr >> 8 & 0xFF, addr & 0xFF] + [0] * (1 + 2 * n))

    def parse(reply):
        data = reply[4:]
        return [data[2 * i] << 8 | data[2 * i + 1] for i in range(n)]
    return out, parse


# ----------------------------------------------------------------------------- encodings
def slot_words(word):
    """A 53-bit slot as its 4 host words (ISA.md §4.1): w0 = [15:0], w1 = [31:16], w2 = [47:32], w3 = [52:48]."""
    return [word & 0xFFFF, word >> 16 & 0xFFFF, word >> 32 & 0xFFFF, word >> 48 & 0x1F]


def port_word(port, producer, mode="blocking", accept=0xF, enable=True):
    """A fabric port register (D-044): [0] en, [1] tap, [5:2] sel, [9:6] accept."""
    sel = S.LEGAL_SOURCES[port].index(producer)
    return int(enable) | int(mode == "tap") << 1 | sel << 2 | (accept & 0xF) << 6


def slot_addr(lane, slot, word):
    return HM["slots"] | lane << 8 | slot << 4 | word


def lane_addr(lane, name):
    return HM["lanes"] + S.HOST_LANE_STRIDE * lane + LW[name]


def load_sequence(image, run=True):
    """Every host write that loads a tripc image, in §14 H1 order, as [(address, [words]), ...]:
    halt, every pin unit's block, owners, every fabric port (unused ones disabled), each used lane's 12
    slots (unused with V = 0) and K, its r0-r3 and STATE, the SRAM, then RUN for the used lanes."""
    seq = [(HM["run"], [0])]
    for u in range(UNITS):
        regs = [int(w, 16) for w in image["pin_regs"][f"U{u}"]]
        seq.append((HM["pin_cfg"] + S.PIN_CFG_STRIDE * u, regs[:PC_WORDS]))
    owners = {pad: 7 for pad in range(8, 24) if pad not in HOST_PADS}
    for pad, unit in image["own"]:
        owners[pad] = unit
    for pad, unit in sorted(owners.items()):
        seq.append((HM["owners"] + pad - 8, [unit]))
    ports = {c: 0 for c in S.FABRIC_CONSUMERS}
    for port, producer, mode, accept in image["connect"]:
        ports[port] = port_word(port, producer, mode, accept)
    seq.append((HM["ports"], [ports[c] for c in S.FABRIC_CONSUMERS]))
    used = sorted(int(name[1:]) for name in image["lanes"])
    for k in used:
        lane = image["lanes"][f"L{k}"]
        words = [int(w, 16) for w in lane["slots"]] + [0] * (12 - len(lane["slots"]))
        for s, w in enumerate(words):               # slots are 16 addresses apart: one transaction each
            seq.append((slot_addr(k, s, 0), slot_words(w)))
        seq.append((slot_addr(k, 12, 0), list(lane["k"])))
        seq.append((lane_addr(k, "r0"), list(lane["regs"]) + [0]))       # r0-r3, then STATE 0
    if image["routines"]:
        seq.append((HM["sram"], list(image["sram"])))
    if run:
        seq.append((HM["run"], [sum(1 << k for k in used)]))
    return seq


# ----------------------------------------------------------------------------- client
class Host:
    """The host API over a full-duplex SPI transfer function `xfer(bytes) -> bytes` (one CS_n-low
    transaction per call)."""

    def __init__(self, xfer):
        self.xfer = xfer

    def write(self, addr, words):
        self.xfer(frame_write(addr, list(words)))

    def read(self, addr, n=1):
        out, parse = frame_read(addr, n)
        return parse(self.xfer(out))

    def ident(self):
        return self.read(HM["version"], 2)                     # [version, id]

    def run(self, lanes_mask):
        self.write(HM["run"], [lanes_mask])

    def halt(self):
        self.write(HM["run"], [0])

    def step(self, lanes_mask):
        self.write(HM["step"], [lanes_mask])

    def time(self):
        return self.read(HM["time"])[0]

    def lane(self, k):
        """Lane k's debug block (§9) as {word name: value}."""
        return dict(zip(S.HOST_LANE_WORDS, self.read(HM["lanes"] + S.HOST_LANE_STRIDE * k,
                                                     len(S.HOST_LANE_WORDS))))

    def unit_flags(self):
        return self.read(HM["unit_flags"], UNITS)

    def clear_unit_flags(self, u, overrun=True, late=True):
        self.write(HM["unit_flags"] + u, [int(overrun) | int(late) << 1])

    def push(self, data, tag=S.TAGS["DATA"]):
        """HOST_IN push; returns False (nothing written) while HOST_IN is not free."""
        if not self.read(HM["host_status"])[0] >> 14 & 1:
            return False
        self.write(HM["host_in"] + tag, [data])
        return True

    def pop(self):
        """HOST_OUT: (tag, data), or None when it holds no token."""
        status = self.read(HM["host_status"])[0]
        if not status >> 15 & 1:
            return None
        return status & 3, self.read(HM["host_out"])[0]

    def load(self, image, run=True):
        for addr, words in load_sequence(image, run):
            self.write(addr, words)


class RegisterModel:
    """The write side of the map in software: applies writes and keeps what each register holds, so a
    sequence can be checked without hardware (slots, K, lane registers, ports, owners, pin blocks, SRAM)."""

    def __init__(self):
        self.mem = {}
        self.run = 0

    def write(self, addr, words):
        for i, w in enumerate(words):
            a = addr + i
            if a == HM["owners"] + 3 or a == HM["owners"] + 6:
                continue                                # host pads ignore owner writes
            if HM["slots"] <= a < HM["slots"] + 0x400 and (a - HM["slots"]) >> 8 & 3 < LANES \
                    and self.run >> ((a - HM["slots"]) >> 8 & 3) & 1:
                continue                                # a running lane's slots are not written
            self.mem[a] = w
            if a == HM["run"]:
                self.run = w

    def slot(self, lane, s):
        w = [self.mem.get(slot_addr(lane, s, i), None) for i in range(4)]
        return None if None in w else w[0] | w[1] << 16 | w[2] << 32 | (w[3] & 0x1F) << 48

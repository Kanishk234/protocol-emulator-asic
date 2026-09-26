"""I2C reference model: open-drain bus resolution, a cycle-level I2C target (register device)
and a bus decoder. Written from the I2C bus specification (NXP UM10204), independent of WARP RTL.

Bus rules used:
- SDA and SCL are wired-AND: a line is low if any device pulls it low, else high (pull-up).
- START: SDA falls while SCL is high. STOP: SDA rises while SCL is high. A START while a
  transfer is in progress is a repeated START.
- Data: SDA may change only while SCL is low; it is sampled on the rising edge of SCL.
- Each byte is 8 bits MSB first, followed by a 9th clock for ACK (SDA low) / NACK (SDA high),
  driven by the receiver.
- The first byte after START is the address: 7 bits + R/W (1 = read).
- A target may hold SCL low (clock stretching); the controller must wait for SCL to rise.

Signals are one value per system clock.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple


def wired_and(*levels: int) -> int:
    return int(all(levels))


@dataclass
class Target:
    """A register-map I2C target at `addr`.

    Write transaction: [addr+W] [reg] [data...]: sets the register pointer, then writes
    data bytes to consecutive registers. Read transaction: [addr+R]: returns bytes from the
    register pointer, auto-incrementing. Unmapped registers read `fill`.
    `stretch`: clocks to hold SCL low after each ACK/NACK bit (clock stretching test).
    `nack_after`: NACK the n-th byte written after the address (the register pointer is byte 1;
    0 = never), then ignore the rest of the transaction.
    """

    addr: int
    regs: Dict[int, int] = field(default_factory=dict)
    nregs: int = 16
    fill: int = 0xFF
    stretch: int = 0
    nack_after: int = 0
    log: List[Tuple[str, int]] = field(default_factory=list)

    def __post_init__(self):
        self._sda_prev = 1
        self._scl_prev = 1
        self._state = "idle"     # idle, addr, write, read, ack_out, ack_in, ignore
        self._bits = 0
        self._shift = 0
        self._ptr = 0
        self._first = True       # next written byte is the register pointer
        self._nwritten = 0
        self._sda_out = 1        # our open-drain output (1 = released)
        self._scl_out = 1
        self._stretch_left = 0
        self._next_after_ack = "idle"
        self._acked = False

    # -- helpers
    def _read_byte(self) -> int:
        return self.regs.get(self._ptr, self.fill) if self._ptr < self.nregs else self.fill

    def step(self, sda_bus: int, scl_bus: int) -> Tuple[int, int]:
        """One system clock. `sda_bus`/`scl_bus` are the resolved bus levels for this clock.
        Returns this target's (sda_out, scl_out) open-drain drives for the next clock."""
        rise = self._scl_prev == 0 and scl_bus == 1
        fall = self._scl_prev == 1 and scl_bus == 0

        if scl_bus == 1 and self._scl_prev == 1 and self._sda_prev != sda_bus:
            if sda_bus == 0:   # START / repeated START
                self.log.append(("start", 0))
                self._state, self._bits, self._shift = "addr", 0, 0
                self._sda_out = 1
            else:              # STOP
                self.log.append(("stop", 0))
                self._state = "idle"
                self._sda_out = 1
            self._sda_prev, self._scl_prev = sda_bus, scl_bus
            return self._sda_out, self._scl_out

        if self._stretch_left:
            self._stretch_left -= 1
            if self._stretch_left == 0:
                self._scl_out = 1

        if rise and self._state in ("addr", "write"):
            self._shift = ((self._shift << 1) | sda_bus) & 0xFF
            self._bits += 1
        elif rise and self._state == "ack_in":
            nack = sda_bus == 1
            self.log.append(("ack_in", int(not nack)))
            self._next_after_ack = "ignore" if nack else "read"
        elif fall:
            if self._state in ("addr", "write") and self._bits == 8:
                byte = self._shift
                self._bits = 0
                if self._state == "addr":
                    if (byte >> 1) == self.addr:
                        self._acked = True
                        if byte & 1 == 0:
                            self._first = True  # a write starts with the register pointer
                        self._next_after_ack = "read" if byte & 1 else "write"
                        self.log.append(("addr", byte))
                    else:
                        self._acked = False
                        self._next_after_ack = "ignore"
                else:
                    self._nwritten += 1
                    if self.nack_after and self._nwritten == self.nack_after:
                        self._acked = False
                        self._next_after_ack = "ignore"
                        self.log.append(("nack_data", byte))
                    else:
                        self._acked = True
                        self._next_after_ack = "write"
                        if self._first:
                            self._ptr = byte
                            self._first = False
                            self.log.append(("ptr", byte))
                        else:
                            self.regs[self._ptr] = byte
                            self.log.append(("wr", byte))
                            self._ptr += 1
                self._sda_out = 0 if self._acked else 1
                self._state = "ack_out"
            elif self._state == "ack_out":
                # end of our ACK clock
                self._sda_out = 1
                self._state = self._next_after_ack
                if self.stretch:
                    self._scl_out = 0
                    self._stretch_left = self.stretch
                if self._state == "read":
                    self._shift = self._read_byte()
                    self.log.append(("rd", self._shift))
                    self._ptr += 1
                    self._bits = 0
                    self._sda_out = (self._shift >> 7) & 1
            elif self._state == "read":
                self._bits += 1
                if self._bits == 8:
                    self._sda_out = 1
                    self._state = "ack_in"
                else:
                    self._sda_out = (self._shift >> (7 - self._bits)) & 1
            elif self._state == "ack_in":
                if self._next_after_ack == "read":
                    self._state = "read"
                    self._shift = self._read_byte()
                    self.log.append(("rd", self._shift))
                    self._ptr += 1
                    self._bits = 0
                    self._sda_out = (self._shift >> 7) & 1
                else:
                    self._state = "ignore"
                    self._sda_out = 1
                if self.stretch:
                    self._scl_out = 0
                    self._stretch_left = self.stretch

        self._sda_prev, self._scl_prev = sda_bus, scl_bus
        return self._sda_out, self._scl_out


@dataclass
class Event:
    kind: str                  # "start", "restart", "stop", "byte"
    value: int = 0             # byte value
    ack: Optional[bool] = None  # for bytes: True = ACK, False = NACK


def decode(sda: Sequence[int], scl: Sequence[int]) -> List[Event]:
    """Decode resolved bus levels into START / repeated START / STOP / byte+ACK events."""
    events: List[Event] = []
    active = False
    bits = 0
    shift = 0
    ps, pc = 1, 1
    for s, c in zip(sda, scl):
        if c == 1 and pc == 1 and s != ps:
            if s == 0:
                events.append(Event("restart" if active else "start"))
                active = True
            else:
                events.append(Event("stop"))
                active = False
            bits = shift = 0
        elif active and pc == 0 and c == 1:  # SCL rising: sample SDA
            if bits < 8:
                shift = (shift << 1) | s
                bits += 1
            else:
                events.append(Event("byte", shift & 0xFF, s == 0))
                bits = shift = 0
        ps, pc = s, c
    return events


def data_changes_only_when_scl_low(sda: Sequence[int], scl: Sequence[int]) -> List[int]:
    """Clock indices where SDA changed while SCL stayed high, other than START/STOP.
    Returns the indices of START/STOP-like transitions for the caller to compare with the
    decoded events; a well-formed controller produces them only when it means to."""
    return [i for i in range(1, len(sda)) if scl[i] == 1 and scl[i - 1] == 1 and sda[i] != sda[i - 1]]

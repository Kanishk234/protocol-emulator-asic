"""1-Wire device: independent reference model (held-out protocol H2, phase 4).

Written from the 1-Wire standard-speed timing (Maxim, "1-Wire Communication Through Software",
AN126, and the DS18B20 datasheet), not from any WARP design. One open-drain line with a pull-up;
the model is stepped once per system clock with the line level and returns its own drive
(1 = released, 0 = pulling low); the bus level is the wired-AND of everyone's drives.

  - Reset: the master holds the line low for >= 480 us. The device answers 15-60 us after the
    line rises (this model: 30 us) with a presence pulse of 60-240 us (this model: 120 us).
  - Write slot: the master pulls low; the device samples the line 15-60 us after the falling
    edge (this model: 30 us): low = 0, high = 1. Bits LSB first.
  - Read slot: the master pulls low for >= 1 us and releases; to send a 0 the device holds the
    line low from the falling edge until 15-60 us after it (this model: 30 us); to send a 1 it
    leaves the line released. Bits LSB first.
  - ROM commands: READ ROM (0x33): the device sends its 64-bit ROM code, LSB first: family code,
    48-bit serial, CRC-8 (x^8 + x^5 + x^4 + 1) of the first 7 bytes.

`log` records what the device saw: ("reset",), ("byte", value), ("rom_sent",), and timing
violations as ("error", text).
"""

RESET_MIN_US = 480
PRESENCE_WAIT_US = 30
PRESENCE_US = 120
SAMPLE_US = 30
HOLD0_US = 30


def crc8(data):
    """Dallas/Maxim 1-Wire CRC-8 (polynomial x^8 + x^5 + x^4 + 1, reflected 0x8C)."""
    crc = 0
    for b in data:
        for _ in range(8):
            mix = (crc ^ b) & 1
            crc >>= 1
            if mix:
                crc ^= 0x8C
            b >>= 1
    return crc


def rom_code(family, serial):
    """The 8-byte ROM: family, 6 serial bytes (LSB first), CRC-8."""
    body = [family] + [(serial >> (8 * i)) & 0xFF for i in range(6)]
    return body + [crc8(body)]


class Device:
    def __init__(self, rom, clk_ns):
        self.rom = list(rom)
        self.us = 1000.0 / clk_ns          # clocks per microsecond
        self.t = 0                         # clock count
        self.prev = 1
        self.fall = None                   # clock of the last falling edge
        self.low_since = None
        self.presence_from = self.presence_to = None
        self.mode = "idle"                 # idle, command, send
        self.bits = []
        self.tx = []                       # bits to send (read slots)
        self.hold_until = None             # driving a 0 in a read slot until this clock
        self.sampled = True
        self.log = []

    def _clocks(self, us):
        return int(round(us * self.us))

    def step(self, line):
        t = self.t
        self.t += 1
        drive = 1
        # edges of the bus
        if self.prev == 1 and line == 0:
            self.fall = t
            self.low_since = t
            self.sampled = False
            if self.mode == "send" and self.tx and self.presence_to is None:
                bit = self.tx.pop(0)
                if bit == 0:
                    self.hold_until = t + self._clocks(HOLD0_US)
                if not self.tx:
                    self.log.append(("rom_sent",))
                    self.mode = "idle"
        if self.prev == 0 and line == 1 and self.low_since is not None:
            low_us = (t - self.low_since) / self.us
            if low_us >= RESET_MIN_US:
                self.log.append(("reset",))
                self.mode = "command"
                self.bits = []
                self.tx = []
                self.presence_from = t + self._clocks(PRESENCE_WAIT_US)
                self.presence_to = self.presence_from + self._clocks(PRESENCE_US)
            self.low_since = None
        # presence pulse
        if self.presence_from is not None and self.presence_from <= t < self.presence_to:
            drive = 0
        elif self.presence_to is not None and t >= self.presence_to:
            self.presence_from = self.presence_to = None
        # a 0 in a read slot
        if self.hold_until is not None:
            if t < self.hold_until:
                drive = 0
            else:
                self.hold_until = None
        # write slots: sample 30 us after the falling edge
        if (self.mode == "command" and not self.sampled and self.fall is not None
                and self.presence_to is None and t - self.fall == self._clocks(SAMPLE_US)):
            self.sampled = True
            self.bits.append(line)
            if len(self.bits) == 8:
                v = sum(b << i for i, b in enumerate(self.bits))
                self.bits = []
                self.log.append(("byte", v))
                if v == 0x33:                          # READ ROM
                    self.mode = "send"
                    self.tx = [(b >> i) & 1 for b in self.rom for i in range(8)]
                else:
                    self.mode = "idle"
        self.prev = line
        return drive

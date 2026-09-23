"""Reference 1-Wire device (a DS18B20-like ROM responder), open drain with a pull-up.

Written from the 1-Wire timing in Maxim AN126 and the DS18B20 datasheet, not from TRIPWIRE
firmware:
- Reset: the controller holds the line low >= 480 us. After the release the device waits
  15-60 us, then pulls low for 60-240 us (presence pulse).
- Every time slot starts with the controller pulling the line low.
  Write: the device samples the line 15-60 us after the falling edge (here: 30 us).
  Read: to send a 0, the device holds the line low until 30 us after the edge (a 1: it does
  nothing). The controller must sample within 15 us of the edge.
- Commands handled: READ ROM (0x33) sends the 8-byte ROM, LSB first. Other bytes are recorded.
Clock-level: step(bus) -> release (1) or pull low (0), at 50 MHz (US clocks per us).
"""

US = 50


def crc8(data):
    """Dallas/Maxim CRC-8 (x^8 + x^5 + x^4 + 1, reflected)."""
    crc = 0
    for byte in data:
        for _ in range(8):
            mix = (crc ^ byte) & 1
            crc >>= 1
            if mix:
                crc ^= 0x8C
            byte >>= 1
    return crc


class OneWireDevice:
    def __init__(self, rom7=(0x28, 0xFF, 0x4C, 0x59, 0x91, 0x16, 0x04), present=True):
        self.rom = list(rom7) + [crc8(rom7)]
        self.present = present
        self.received = []                  # bytes written by the controller, since reset
        self.resets = 0
        self.drive = 1
        self._prev = 1
        self._t = 0
        self._fall = None                   # time of the controller's last falling edge
        self._release_at = None
        self._presence = None               # (start, end) of a scheduled presence pulse
        self._sample_at = None
        self._rx = []
        self._tx = []                       # bits still to send in read slots

    def step(self, bus):
        t = self._t
        if self._prev == 1 and bus == 0 and self.drive == 1:       # the controller's edge
            self._fall = t
            if self._tx:                                            # read slot
                if self._tx.pop(0) == 0:
                    self.drive, self._release_at = 0, t + 30 * US
            else:
                self._sample_at = t + 30 * US
        if self._prev == 0 and bus == 1 and self._fall is not None:
            if t - self._fall >= 400 * US:                          # reset pulse
                self.resets += 1
                self._rx, self._tx, self._sample_at, self.received = [], [], None, []
                if self.present:
                    self._presence = (t + 30 * US, t + 150 * US)
            self._fall = None
        if self._sample_at is not None and t == self._sample_at:
            self._sample_at = None
            self._rx.append(bus)
            if len(self._rx) == 8:
                byte = sum(b << i for i, b in enumerate(self._rx))
                self._rx = []
                self.received.append(byte)
                if byte == 0x33:                                    # READ ROM
                    self._tx = [(b >> i) & 1 for b in self.rom for i in range(8)]
        if self._presence and t == self._presence[0]:
            self.drive = 0
        if self._presence and t == self._presence[1]:
            self.drive, self._presence = 1, None
        if self._release_at is not None and t >= self._release_at:
            self.drive, self._release_at = 1, None
        self._prev = bus
        self._t += 1
        return self.drive

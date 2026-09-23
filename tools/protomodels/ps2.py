"""Reference PS/2 device (e.g. a keyboard), open-drain CLK and DATA with pull-ups.

Written from the PS/2 protocol description (Chapweske, "The PS/2 Mouse/Keyboard Protocol"),
not from TRIPWIRE firmware:
- The device always generates the clock (10-16.7 kHz).
- Device to host: 11-bit frames (start 0, 8 data bits LSB first, odd parity, stop 1). Data
  changes while CLK is high; the host reads it on the falling edge.
- Host to device: the host holds CLK low (>= 100 us), pulls DATA low (the start bit) and
  releases CLK. The device then clocks in 8 data bits, parity and stop (the host changes DATA
  while CLK is low; the device reads it while CLK is high), and ACKs by pulling DATA low for
  one more clock.
Clock-level: step(clk_bus, data_bus) -> (clk_release, data_release), 1 = released.
"""


def odd_parity(byte):
    return 1 - (bin(byte).count("1") & 1)


class PS2Device:
    def __init__(self, half, send=(), bad_parity=()):
        self.h = half                       # half a clock period, in 50 MHz clocks
        self.queue = list(send)
        self.bad_parity = set(bad_parity)   # indices of sent frames with a wrong parity bit
        self.received = []                  # (byte, parity_ok, stop_ok) from the host
        self.clk = self.data = 1
        self._gen = self._run()
        next(self._gen)
        self._bus = (1, 1)
        self._sent = 0
        self.frames_sent = 0                # completed device-to-host frames

    def step(self, clk_bus, data_bus):
        self._bus = (clk_bus, data_bus)
        self._gen.send(self._bus)
        return self.clk, self.data

    def _wait(self, n):
        for _ in range(n):
            yield

    def _run(self):
        h = self.h
        yield
        while True:
            clk, data = self._bus
            if not clk:                                 # host inhibit: wait for the release
                while not self._bus[0]:
                    yield
                continue
            if not data:                                # CLK high, DATA low: request to send
                yield from self._receive()
                yield                                   # see the bus after our own ACK release
                continue
            if self.queue:
                for _ in range(4 * h):                  # bus idle for a while, then send a frame
                    if self._bus != (1, 1):
                        break
                    yield
                else:
                    yield from self._send(self.queue.pop(0))
                    yield
                continue
            yield

    def _send(self, byte):
        par = odd_parity(byte) ^ (1 if self._sent in self.bad_parity else 0)
        self._sent += 1
        bits = [0] + [(byte >> i) & 1 for i in range(8)] + [par, 1]
        for b in bits:
            self.data = b                               # change while CLK is high
            yield from self._wait(self.h // 2)
            self.clk = 0                                # host reads on this falling edge
            yield from self._wait(self.h)
            self.clk = 1
            yield from self._wait(self.h - self.h // 2)
        self.data = 1
        self.frames_sent += 1

    def _receive(self):
        h, bits = self.h, []
        yield from self._wait(h // 2)
        for i in range(10):                             # 8 data, parity, stop
            self.clk = 0
            yield from self._wait(h)
            self.clk = 1                                # read while CLK is high
            yield from self._wait(h // 2)
            bits.append(self._bus[1])
            if i == 9:
                self.data = 0                           # ACK: DATA low while CLK is still high,
            yield from self._wait(h - h // 2)           # then one more clock pulse
        self.clk = 0
        yield from self._wait(h)
        self.clk = 1
        yield from self._wait(h)
        self.data = 1
        byte = sum(b << i for i, b in enumerate(bits[:8]))
        self.received.append((byte, bits[8] == odd_parity(byte), bits[9] == 1))

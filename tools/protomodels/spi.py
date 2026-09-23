"""Reference SPI target (peripheral), mode 0 (CPOL = 0, CPHA = 0), MSB first.

Written from the SPI mode definitions, not from TRIPWIRE firmware: with CS low, the
target samples MOSI on each SCK rising edge and changes MISO on each falling edge; the
first MISO bit is valid as soon as CS falls. It answers each byte with the byte it
received before it (the first answer is `first`), so both directions are checked.

Clock-level: step(sck, mosi, cs) once per 50 MHz clock with the pad levels it sees;
returns the MISO level it drives from the next clock on (1 while CS is high).
"""


class SPIController:
    """Reference SPI controller, mode 0, MSB first.

    Per transfer: CS falls, MOSI bit 7 is set up, then for each bit SCK rises (MISO is
    sampled at that clock) and falls (MOSI changes), with `half` clocks per phase. CS
    rises `half` clocks after the last falling edge. step(miso) once per clock; the
    outputs sck/mosi/cs apply from the next clock.
    """

    def __init__(self, half, gap=None, tcss=None):
        """half: clocks per SCK phase; gap: CS high time between transfers;
        tcss: clocks from CS falling to the first SCK rise (default: half)."""
        if half < 1:
            raise ValueError("half period must be >= 1 clock")
        self.h = half
        self.gap = gap or 2 * half
        self.tcss = tcss or half
        self.ops = []
        self.results = []           # bytes read on MISO, one list per transfer
        self.sck, self.mosi, self.cs = 0, 0, 1
        self._gen = None

    def transfer(self, data, bits=None):
        """Clock `data` out (and as many bits in); bits < 8*len(data) aborts mid-transfer."""
        self.ops.append((bytes(data), 8 * len(data) if bits is None else bits))

    def done(self):
        return self._gen is False

    def step(self, miso):
        if self._gen is None:
            self._gen = self._run()
            next(self._gen)
        if self._gen is not False:
            try:
                self._gen.send(miso)
            except StopIteration:
                self._gen = False
        return self.sck, self.mosi, self.cs

    def _hold(self, n):
        v = None
        for _ in range(n):
            v = yield
        return v

    def _run(self):
        h = self.h
        yield
        for data, nbits in self.ops:
            self.cs, self.sck = 1, 0
            yield from self._hold(self.gap)
            self.cs = 0
            bits = [(byte >> i) & 1 for byte in data for i in range(7, -1, -1)][:nbits]
            got, b = [], 0
            for k, bit in enumerate(bits):
                self.mosi = bit                       # set while SCK is low
                # the last low-phase clock hands back MISO as it is in the clock where
                # SCK rises: that is the value on the wire at the rising edge
                miso = yield from self._hold(self.tcss if k == 0 else h)
                self.sck = 1
                b = (b << 1) | miso
                yield from self._hold(h)
                self.sck = 0
                if k % 8 == 7:                        # only complete bytes are recorded
                    got.append(b)
                    b = 0
            yield from self._hold(h)
            self.cs = 1
            self.results.append(got)
        yield from self._hold(self.gap)


class SPITarget:
    def __init__(self, first=0xA5):
        self.next_tx = first
        self.received = []
        self._prev = None
        self._rx = 0
        self._bits = 0
        self._out = 0
        self.miso = 1

    def step(self, sck, mosi, cs):
        prev = self._prev
        self._prev = (sck, cs)
        if cs:
            self.miso = 1
            return self.miso
        if prev is None or prev[1] == 1:                  # CS just fell: first bit out
            self._out, self._bits, self._rx = self.next_tx, 0, 0
            self.miso = (self._out >> 7) & 1
            return self.miso
        if sck and not prev[0]:                            # rising edge: sample MOSI
            self._rx = (self._rx << 1) | mosi
            self._bits += 1
            if self._bits == 8:
                self.received.append(self._rx)
                self.next_tx, self._rx, self._bits = self._rx, 0, 0
        elif not sck and prev[0]:                          # falling edge: next MISO bit
            if self._bits == 0:
                self._out = self.next_tx
            self.miso = (self._out >> (7 - self._bits)) & 1
        return self.miso

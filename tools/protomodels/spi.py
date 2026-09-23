"""Reference SPI target (peripheral), mode 0 (CPOL = 0, CPHA = 0), MSB first.

Written from the SPI mode definitions, not from TRIPWIRE firmware: with CS low, the
target samples MOSI on each SCK rising edge and changes MISO on each falling edge; the
first MISO bit is valid as soon as CS falls. It answers each byte with the byte it
received before it (the first answer is `first`), so both directions are checked.

Clock-level: step(sck, mosi, cs) once per 50 MHz clock with the pad levels it sees;
returns the MISO level it drives from the next clock on (1 while CS is high).
"""


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

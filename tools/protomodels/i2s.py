"""Reference I2S models (Philips I2S bus specification, 1986/1996), written from the spec, not
from TRIPWIRE firmware.

- SD is MSB first; the transmitter changes SD and WS on the falling edge of SCK (BCLK), the
  receiver samples on the rising edge.
- WS selects the channel (0 = left, 1 = right) and changes one clock period before the MSB of the
  channel's word, so the bit clocked while WS has just changed is the previous word's LSB.
"""


class I2SReceiver:
    """Decodes (sck, ws, sd) levels into [("L"|"R", word)], word length taken from WS."""

    def __init__(self):
        self.words = []
        self._prev_sck = 0
        self._ws_prev = None
        self._bits = []
        self._started = True        # the bus starts idle: the first word is whole

    def step(self, sck, ws, sd):
        if sck and not self._prev_sck:                      # rising edge: sample
            self._bits.append(sd)
            if self._ws_prev is not None and ws != self._ws_prev:
                # this bit is the LSB of the word for channel _ws_prev; the next word starts now
                if self._started:
                    word = sum(b << (len(self._bits) - 1 - i) for i, b in enumerate(self._bits))
                    self.words.append(("R" if self._ws_prev else "L", word, len(self._bits)))
                self._started = True
                self._bits = []
            self._ws_prev = ws
        self._prev_sck = sck


class I2SADC:
    """The data output of an I2S ADC/codec: drives SD from its own samples, following the
    controller's SCK and WS. WS is latched on the rising edge of SCK (as every I2S receiver and
    transmitter does); after a latched change, the new channel's MSB goes out on the next falling
    edge. Returns the SD level for the current clock."""

    def __init__(self, samples, bits=16):
        self.samples = list(samples)                        # [(left, right)]
        self.bits = bits
        self.sd = 0
        self._prev_sck = 0
        self._ws = None
        self._load = None
        self._shift = []

    def step(self, sck, ws):
        if sck and not self._prev_sck:                      # rising edge: latch WS
            if self._ws is not None and ws != self._ws:
                self._load = ws
            self._ws = ws
        elif not sck and self._prev_sck:                    # falling edge: drive the next bit
            if self._load is not None:
                ch, self._load = self._load, None
                word = 0
                if self.samples:
                    word = self.samples[0][ch]
                    if ch:
                        self.samples.pop(0)
                self._shift = [(word >> (self.bits - 1 - i)) & 1 for i in range(self.bits)]
            self.sd = self._shift.pop(0) if self._shift else 0
        self._prev_sck = sck
        return self.sd

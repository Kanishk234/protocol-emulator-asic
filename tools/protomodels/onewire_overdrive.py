"""Independent DS2431-like ROM-layer responder with real speed entry/exit.

Only ROM READ (33) and Overdrive-Skip ROM (3C) are implemented, not EEPROM
functions. Timing comes from DS2431 rev16, not firmware or RTL. Ideal digital
pull-up; no analog rise time or parasite-power model.
"""
from .onewire import US, crc8


class OverdriveROMDevice:
    def __init__(self, rom7=(0x2D, 0x91, 0x02, 0xA5, 0x7E, 0x13, 0x44), *,
                 present=True, presence_high=None, presence_low=None):
        self.rom = list(rom7) + [crc8(rom7)]
        self.present = present
        self.overdrive = False
        self.drive = 1
        self.resets = []
        self.received = []
        self.history = []
        self.entries = 0
        self.presence_high, self.presence_low = presence_high, presence_low
        self.t = 0
        self.prev = 1
        self.fall = None
        self.fall_fast = False
        self.sample_at = self.release_at = self.presence = None
        self.rx, self.tx = [], []
        self.rom_phase = True

    def step(self, bus):
        t = self.t
        if not self.present:
            self.drive = 1
            self.prev, self.t = bus, t + 1
            return 1
        if self.prev and not bus and self.drive:
            self.fall, self.fall_fast = t, self.overdrive
            if self.tx:
                if self.tx.pop(0) == 0:
                    # Hold zero only through the allowed sampling endpoint.
                    # This catches controllers that sample too late.
                    self.drive = 0
                    self.release_at = t + (2 if self.overdrive else 15) * US
            else:
                self.sample_at = t + (3 if self.overdrive else 30) * US
        if not self.prev and bus and self.fall is not None:
            width = t - self.fall
            fast_reset = self.fall_fast and 48*US <= width <= 80*US
            standard_reset = 480*US <= width <= 640*US
            if fast_reset or standard_reset:
                self.overdrive = bool(fast_reset)
                self.resets.append((self.overdrive, width))
                self.received, self.rx, self.tx = [], [], []
                self.sample_at = self.release_at = None
                self.rom_phase = True
                hi = self.presence_high
                lo = self.presence_low
                if hi is None: hi = (4 if self.overdrive else 30) * US
                if lo is None: lo = (16 if self.overdrive else 120) * US
                self.presence = (t + hi, t + hi + lo)
            self.fall = None
        if self.sample_at == t:
            self.sample_at = None
            self.rx.append(bus)
            if len(self.rx) == 8:
                byte = sum(b << i for i,b in enumerate(self.rx))
                self.rx = []
                self.received.append(byte)
                self.history.append((self.overdrive, byte))
                if self.rom_phase and byte == 0x3C:
                    self.overdrive, self.rom_phase = True, False
                    self.entries += 1
                elif self.rom_phase and byte == 0x33:
                    self.tx = [(b >> i) & 1 for b in self.rom for i in range(8)]
                    self.rom_phase = False
        if self.presence is not None and t == self.presence[0]:
            self.drive = 0
        if self.presence is not None and t == self.presence[1]:
            self.drive, self.presence = 1, None
        if self.release_at is not None and t >= self.release_at:
            self.drive, self.release_at = 1, None
        self.prev, self.t = bus, t + 1
        return self.drive

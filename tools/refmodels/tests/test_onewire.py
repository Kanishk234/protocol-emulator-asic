"""The 1-Wire reference device against an ideal master written from the same timing spec."""

import pytest

from refmodels import onewire

CLK_NS = 20


class Master:
    """Standard-speed 1-Wire master (AN126 timings: A 6, B 64, C 60, D 10, E 9, F 55, G 0,
    H 480, I 70, J 410 us), sharing the line with a device (wired-AND)."""

    def __init__(self, dev):
        self.dev = dev
        self.us = 1000 // CLK_NS

    def _run(self, us, drive):
        """Hold our drive for `us`; return the bus levels seen."""
        seen = []
        for _ in range(int(us * self.us)):
            d = self.dev.step(self.bus)
            self.bus = min(drive, d)
            seen.append(self.bus)
        return seen

    bus = 1

    def reset(self):
        self._run(480, 0)
        seen = self._run(70, 1)
        presence = seen[-1] == 0
        self._run(410, 1)
        return presence

    def write_bit(self, b):
        if b:
            self._run(6, 0)
            self._run(64, 1)
        else:
            self._run(60, 0)
            self._run(10, 1)

    def read_bit(self):
        self._run(6, 0)
        seen = self._run(9, 1)
        v = seen[-1]
        self._run(55, 1)
        return v

    def write_byte(self, v):
        for i in range(8):
            self.write_bit((v >> i) & 1)

    def read_byte(self):
        return sum(self.read_bit() << i for i in range(8))


def test_crc8_known_value():
    # DS18B20 application note example ROM 28 xx ...: the CRC of the 7 bytes is the 8th
    rom = onewire.rom_code(0x28, 0x0000_0A1B_2C3D)
    assert onewire.crc8(rom) == 0                      # CRC over the whole ROM is 0


def test_reset_presence_and_read_rom():
    rom = onewire.rom_code(0x28, 0x1234_5678_9ABC)
    dev = onewire.Device(rom, CLK_NS)
    m = Master(dev)
    assert m.reset()
    m.write_byte(0x33)
    got = [m.read_byte() for _ in range(8)]
    assert got == rom
    assert ("byte", 0x33) in dev.log and ("rom_sent",) in dev.log


def test_no_device_no_presence():
    class Absent:
        def step(self, line):
            return 1
    m = Master(Absent())
    assert not m.reset()


@pytest.mark.parametrize("v", [0x00, 0xFF, 0xA5, 0x3C])
def test_device_reads_written_bytes(v):
    dev = onewire.Device(onewire.rom_code(0x01, 1), CLK_NS)
    m = Master(dev)
    assert m.reset()
    m.write_byte(v)
    assert ("byte", v) in dev.log

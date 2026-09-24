"""L3-SMBUS on the model: programs/smbus.trw (PEC computed on chip) against the reference SMBus device."""

import pytest

from kernels import load_program
from protomodels.smbus import SMBusDevice, crc8
from tripsim import Chip
from tripsim.isa import TAG_CTRL, TAG_DATA, TAG_EVENT

SDA, SCL = 0, 1
ADDR = 0x2C
AW, AR = ADDR << 1, ADDR << 1 | 1
S, P = (0, TAG_EVENT), (0x8000, TAG_EVENT)
W = lambda b: (b, TAG_DATA)
PEC = (0x8000, TAG_DATA)
R = lambda nack: (nack, TAG_CTRL)


def run(chip, dev, clocks):
    got = []
    for _ in range(clocks):
        _, uio, oe = chip.outputs()
        low = lambda bit: ((oe >> bit) & 1) and not ((uio >> bit) & 1)
        scl = int(dev.scl and not low(SCL))
        sda = int(dev.sda and not low(SDA))
        chip.uio_in = (0xFF & ~3) | (scl << SCL) | (sda << SDA)
        chip.step()
        dev.step(scl, sda)
        while chip.host_out:                    # the host reads its FIFO as it goes
            got.append(chip.host_out.popleft())
    return got


def make(period, dev):
    chip = Chip(lanes=1)
    chip.settle_inputs(uio=0xFF)
    load_program(chip, "smbus", PERIOD=period)
    return chip


@pytest.mark.parametrize("period", [500, 124])          # 100 kHz and 400 kHz
def test_write_word_and_read_word_with_pec(period):
    dev = SMBusDevice(ADDR, regs={0x05: 0xBEEF})
    chip = make(period, dev)
    seq = [S, W(AW), W(0x10), W(0x34), W(0x12), PEC, P,               # Write Word 0x1234 to 0x10 + PEC
           S, W(AW), W(0x05), S, W(AR), R(0), R(0), R(1), P,          # Read Word 0x05 + PEC
           S, W(AW), W(0x10), S, W(AR), R(0), R(0), R(1), P]          # read 0x10 back
    for d, t in seq:
        chip.host_push(d, t)
    got = run(chip, dev, 140 * 9 * period)
    ack = (TAG_DATA, 0)
    pec5 = crc8([AW, 0x05, AR, 0xEF, 0xBE])
    pec10 = crc8([AW, 0x10, AR, 0x34, 0x12])
    assert got == ([ack] * 5 + [(TAG_EVENT, 0)]
                   + [ack] * 3 + [(TAG_DATA, 0xEF), (TAG_DATA, 0xBE), (TAG_DATA, pec5), (TAG_EVENT, 0)]
                   + [ack] * 3 + [(TAG_DATA, 0x34), (TAG_DATA, 0x12), (TAG_DATA, pec10), (TAG_EVENT, 0)])
    assert dev.writes == [(0x10, [0x34, 0x12], True)]                  # the device accepted our PEC


def test_bad_pec_from_the_device_is_reported():
    class Bad(SMBusDevice):
        corrupted = False

        def step(self, scl, sda):
            r = super().step(scl, sda)
            if len(self.read_data) == 3 and not self.corrupted:
                self.read_data[2] ^= 0x01                # corrupt the PEC byte it will send
                self.corrupted = True
            return r

    dev = Bad(ADDR, regs={0x05: 0x1234})
    chip = make(500, dev)
    for d, t in [S, W(AW), W(0x05), S, W(AR), R(0), R(0), R(1), P]:
        chip.host_push(d, t)
    got = run(chip, dev, 40 * 9 * 500)
    events = [d for t, d in got if t == TAG_EVENT]
    assert dev.corrupted and len(events) == 1 and events[0] != 0


def test_bad_pec_to_the_device_is_rejected_by_it():
    """Negative control for the reference device: a wrong PEC (sent as data) is refused."""
    dev = SMBusDevice(ADDR)
    chip = make(500, dev)
    wrong = crc8([AW, 0x10, 0x34, 0x12]) ^ 0x80
    for d, t in [S, W(AW), W(0x10), W(0x34), W(0x12), W(wrong), P]:
        chip.host_push(d, t)
    run(chip, dev, 30 * 9 * 500)
    assert dev.writes == [(0x10, [0x34, 0x12], False)] and 0x10 not in dev.regs

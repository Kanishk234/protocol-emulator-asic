"""USB low-speed FEASIBILITY on the model (not a support claim): programs/usb_ls.trw enumerated
by the reference USB host (GET_DESCRIPTOR, SET_ADDRESS), plus sigrok's usb_signalling/usb_packet."""

import re
import shutil
import subprocess

from kernels import load_program
from protomodels.usb import USBLSHost
from tripsim import Chip
from tripsim.vcd import VcdRecorder

DM, DP = 0, 1                                  # uio0 = D-, uio1 = D+
DESC = [0x12, 0x01, 0x10, 0x01, 0x00, 0x00, 0x00, 0x08, 0x34, 0x12, 0x78, 0x56,
        0x00, 0x01, 0x00, 0x00, 0x00, 0x01]


class Bus:
    def __init__(self, vcd=False):
        self.chip = Chip(lanes=1)
        self.chip.settle_inputs(uio=0xFF & ~(1 << DP))           # J: D- high, D+ low
        load_program(self.chip, "usb_ls")
        self.host = USBLSHost()
        self.dp, self.dm, self.contention = 0, 1, 0
        self.rec = None
        if vcd:
            self.rec = VcdRecorder({"dp": lambda c: self.dp, "dm": lambda c: self.dm})
            self.chip.observers.append(self.rec)

    def run(self, clocks):
        for _ in range(int(clocks)):
            _, uio, oe = self.chip.outputs()
            dev_oe = (oe >> DM) & 1
            hdp, hdm, hoe = self.host.drive[0], self.host.drive[1], self.host.oe
            if hoe and dev_oe:
                self.contention += 1
            if hoe:
                self.dp, self.dm = hdp, hdm
            elif dev_oe:
                self.dp, self.dm = (uio >> DP) & 1, (uio >> DM) & 1
            else:
                self.dp, self.dm = 0, 1                              # pull-down D+, pull-up D-
            self.chip.uio_in = (0xFF & ~3) | self.dp << DP | self.dm << DM
            self.chip.step()
            self.host.step(self.dp, self.dm)


BIT = 50e6 / 1.5e6


def test_enumeration_get_descriptor_set_address(tmp_path):
    bus = Bus(vcd=True)
    bus.run(20 * BIT)
    bus.host.get_descriptor(0, 64)
    bus.host.set_address(0, 5)
    bus.host.get_descriptor(5, 18)
    bus.host.get_descriptor(0, 18)                                  # the old address: silence
    bus.run(2400 * BIT)                                            # ~400-600 bit times per transfer
    r = bus.host.results
    assert r[0] == ("get", 0, DESC)                                  # 8 + 8 + 2 bytes, DATA1/0/1
    assert r[1] == ("set", 0, [])
    assert r[2] == ("get", 5, DESC)
    assert r[3] == ("get", 0, None)
    assert bus.contention == 0
    assert max(bus.host.delays) <= 7.5, bus.host.delays               # device turnaround (bit times)
    if shutil.which("sigrok-cli"):
        bus.rec.write(tmp_path / "usb.vcd")
        out = subprocess.run(["sigrok-cli", "-i", str(tmp_path / "usb.vcd"), "-I", "vcd", "-P",
                              "usb_signalling:dp=dp:dm=dm:signalling=low-speed,usb_packet",
                              "-A", "usb_packet=packet"], capture_output=True, text=True, check=True).stdout
        lines = out.splitlines()
        # the device's data packets are the ones right after an IN token
        device = [re.findall(r"[0-9A-F]{2}", lines[i + 1].split("[", 1)[1])
                  for i, l in enumerate(lines[:-1]) if " IN ADDR" in l and "DATA" in lines[i + 1]]
        payload = [int(x, 16) for chunk in device for x in chunk]
        assert payload == DESC + DESC, out                               # both GET_DESCRIPTORs, exact
        assert [len(c) for c in device] == [8, 8, 2, 0, 8, 8, 2], out    # + SET_ADDRESS status (0)
        # address 0: 2 answered setups, then 3 unanswered tries after SET_ADDRESS
        assert out.count("SETUP ADDR 0") == 5 and out.count("SETUP ADDR 5") == 1, out


def test_bad_crcs_get_no_answer():
    bus = Bus()
    bus.run(20 * BIT)
    bus.host.bad_token(0)                                            # IN with a bad CRC-5
    bus.host.get_descriptor(0, 18, corrupt_setup_once=True)          # SETUP data with a bad CRC-16
    bus.run(1400 * BIT)
    assert bus.host.results[0] == ("badtok", 0, None)
    assert bus.host.log[0] == ("setup", None)                        # no ACK for the bad CRC-16 ...
    assert bus.host.results[1] == ("get", 0, DESC)                   # ... the retry works

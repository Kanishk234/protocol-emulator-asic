"""L3-SPI-T on the model: SPI target kernel against the reference controller and sigrok."""

import re
import shutil
import subprocess

import pytest

from kernels import spi_target
from protomodels.spi import SPIController
from tripsim import Chip
from tripsim.isa import TAG_EVENT
from tripsim.vcd import VcdRecorder

MOSI, SCK, CS, MISO = 0, 1, 2, 0
T1_OUT, T1_IN = [0x01, 0x02, 0x80], [0x5A, 0x3C, 0x0F]      # first MISO bits 0: an undriven
T2_OUT, T2_IN = [0xFF, 0x00], [0x55, 0xAA]                  # (pulled-up) MISO would show as 1
TCSS = 4                                                    # CS setup used by the tests (clocks)


def run(half, vcd=None, max_clocks=200_000, miso_edge="rise", tcss=TCSS):
    chip = Chip(lanes=1)
    chip.settle_inputs(ui=1 << CS)                         # CS high (deselected) through reset
    spi_target.load(chip, mosi=MOSI, sck=SCK, cs=CS, miso=MISO, miso_edge=miso_edge)
    for b in T1_IN:
        chip.host_push(b)
    # CS high >= 400 ns between transfers; CS setup >= 4 clocks (80 ns). The target needs
    # >= 3 clocks: CS passes the synchroniser before MISO's output driver turns on.
    ctrl = SPIController(half, gap=max(2 * half, 20), tcss=tcss)
    ctrl.transfer(T1_OUT)
    ctrl.transfer(T2_OUT)
    rec = None
    if vcd:
        rec = VcdRecorder({"sck": lambda c: (c.ui_in >> SCK) & 1, "mosi": lambda c: (c.ui_in >> MOSI) & 1,
                           "cs": lambda c: (c.ui_in >> CS) & 1,
                           "miso": lambda c: (c.outputs()[1] >> MISO) & 1})
        chip.observers.append(rec)
    oe_run = oe_while_deselected = 0                         # longest MISO drive after CS rose
    pushed2 = False
    for _ in range(max_clocks):
        _, uio, oe = chip.outputs()
        miso_oe = (oe >> MISO) & 1
        oe_run = oe_run + 1 if (ctrl.cs and miso_oe) else 0
        oe_while_deselected = max(oe_while_deselected, oe_run)
        miso = (uio >> MISO) & 1 if miso_oe else 1          # pulled up when not driven
        sck, mosi, cs = ctrl.step(miso)
        chip.ui_in = (sck << SCK) | (mosi << MOSI) | (cs << CS)
        chip.step()
        if len(ctrl.results) == 1 and not pushed2:            # host refills between transfers
            for b in T2_IN:
                chip.host_push(b)
            pushed2 = True
        if ctrl.done():
            break
    else:
        raise AssertionError("SPI transfers did not finish")
    chip.run_for(20)                                       # let the last CS event reach the host
    if rec:
        rec.write(vcd)
    return chip, ctrl, oe_while_deselected


def host_view(chip):
    return [("CS", d >> 15) if t == TAG_EVENT else d for t, d in chip.host_out]


@pytest.mark.parametrize("miso_edge", ["rise", "fall"])
@pytest.mark.parametrize("half", [25, 5, 4])              # SCK 1 MHz, 5 MHz, 6.25 MHz
def test_spi_target_mode0(half, miso_edge):
    chip, ctrl, oe_bad = run(half, miso_edge=miso_edge)
    assert ctrl.results == [T1_IN, T2_IN]                  # MISO
    assert host_view(chip) == [("CS", 0), *T1_OUT, ("CS", 1), ("CS", 0), *T2_OUT, ("CS", 1)]
    # output disable time: CS passes the 2-clock synchroniser, so MISO is released <= 3 clocks (60 ns) late
    assert oe_bad <= 3, f"MISO driven {oe_bad} clocks after CS rose"
    assert all(u.stats["bad_tokens"] == 0 for u in chip.pins)


@pytest.mark.skipif(shutil.which("sigrok-cli") is None, reason="sigrok-cli not installed")
def test_spi_target_sigrok(tmp_path):
    run(5, vcd=tmp_path / "spit.vcd")
    got = {}
    for cls in ("mosi-data", "miso-data"):
        out = subprocess.run(["sigrok-cli", "-i", str(tmp_path / "spit.vcd"), "-I", "vcd",
                              "-P", "spi:clk=sck:mosi=mosi:miso=miso:cs=cs", "-A", f"spi={cls}"],
                             capture_output=True, text=True, check=True).stdout
        got[cls] = [int(h, 16) for h in re.findall(r"spi-\d+: ([0-9A-F]{2})\b", out)]
    assert got["mosi-data"] == T1_OUT + T2_OUT
    assert got["miso-data"] == T1_IN + T2_IN


def fastest_half(lo=1, hi=8, miso_edge="rise"):
    best = None
    for h in range(hi, lo - 1, -1):
        try:
            chip, ctrl, oe_bad = run(h, miso_edge=miso_edge)
        except AssertionError:
            break
        if ctrl.results != [T1_IN, T2_IN] or oe_bad > 3:
            break
        best = h
    return best


def test_spi_target_speed():
    """MISO moves 3 clocks after the SCK edge it follows (2 sync + 1 register)."""
    rise, fall = fastest_half(miso_edge="rise"), fastest_half(miso_edge="fall")
    assert fall is not None and fall <= 3, f"fall: fastest half period {fall}"
    assert rise is not None and rise < fall, f"rise ({rise}) should beat fall ({fall})"


def test_spi_target_abort_resyncs():
    """A transfer aborted after 4 bits must not shift the framing of the next one (pin C, §14 P15)."""
    chip = Chip(lanes=1)
    chip.settle_inputs(ui=1 << CS)
    spi_target.load(chip, mosi=MOSI, sck=SCK, cs=CS, miso=MISO)
    for b in [0x96, 0x5A]:                        # 0x96 is cut after 4 bits and discarded;
        chip.host_push(b)                         # 0x5A (not yet taken by the pin unit) comes next
    ctrl = SPIController(5, gap=20, tcss=4)
    ctrl.transfer([0xF0], bits=4)                 # aborted: 4 bits, then CS rises
    ctrl.transfer([0xC3])                         # a full byte must be received intact
    while not ctrl.done():
        _, uio, oe = chip.outputs()
        sck, mosi, cs = ctrl.step((uio >> MISO) & 1 if (oe >> MISO) & 1 else 1)
        chip.ui_in = (sck << SCK) | (mosi << MOSI) | (cs << CS)
        chip.step()
    chip.run_for(20)
    assert host_view(chip) == [("CS", 0), ("CS", 1), ("CS", 0), 0xC3, ("CS", 1)]
    assert ctrl.results[1] == [0x5A]              # a whole host byte, never the rest of 0x96


def test_spi_target_cs_setup():
    """MISO's driver turns on 3 clocks after CS falls: a 2-clock CS setup must fail, 3 must pass."""
    ok = lambda t: run(25, tcss=t)[1].results == [T1_IN, T2_IN]
    assert not ok(2) and ok(3)

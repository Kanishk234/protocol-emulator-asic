"""Phase 2 L2 deterministic RTL/tripsim lockstep and RTL mutation checks."""

from __future__ import annotations

import os
import pathlib
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, ReadOnly, RisingEdge, Timer

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "tools" / "host"), str(pathlib.Path(__file__).parent)]

import tripwire_spec as S  # noqa: E402
from tripsim import Chip, PAD_UO  # noqa: E402
from tripsim.pinunit import PinConfig  # noqa: E402
from tripsim import pinregs  # noqa: E402
from tripsim.lockstep import first_difference  # noqa: E402
from host import frame_write, slot_words  # noqa: E402
from adapter import CandidateMap, model_snapshot, rtl_snapshot  # noqa: E402

RTL_DIR = pathlib.Path(os.environ.get("RTL_DIR", "/tmp/r4-bitsync-work/src"))
RTL_REV = os.environ.get("RTL_REV", "unknown")
CSN, SCK, MOSI, MISO = 4, 5, 6, 3


def slot(**fields):
    fields.setdefault("V", 1)
    word = 0
    for name, value in fields.items():
        lsb, width = S.SLOT_FIELDS[name]
        word |= value << lsb
    return word


PIN_CONFIG = dict(pin_a=0, txmode="level", rxmode="shift_rx", idle=1,
                  autorearm=True, period=8, sampleofs=0.5, presc=1,
                  nbits=9, rx_nbits=10)


def make_setup():
    """Two competing RX consumers test priority on the same received token."""
    op, dst, asrc = S.OPS, S.DST, S.ASRC
    words = {
        (0, 0): slot(OP=op["MOV"], DST=dst["r0"], ASRC=asrc["I0"], DQ=1),
        (0, 1): slot(OP=op["MOV"], DST=dst["r1"], ASRC=asrc["I0"], DQ=1),
    }
    chip = Chip(lanes=2, pin_units=4, slots=12, sram_words=512)
    return chip, words


class HostSPI:
    """Minimal host SPI master using the project frame encoder."""

    def __init__(self, dut, chip: Chip, cmap: CandidateMap):
        self.d = dut
        self.chip = chip
        self.cmap = cmap
        self.ui = (1 << CSN) | 1
        self.monitor = None

    async def _one_from_falling(self):
        await ReadOnly()
        ui, uio = _bits(self.d.ui_in), _bits(self.d.uio_in)
        wr = _bits(self.d.dbg_host_wr)
        address, value = _bits(self.d.dbg_host_wa), _bits(self.d.dbg_host_wd)
        self.chip.ui_in, self.chip.uio_in = ui, uio
        if wr and address != self.cmap.defs["TRW_HA_RUN"]:
            _apply_host_write(self.chip, self.cmap, address, value)
        await RisingEdge(self.d.clk)
        self.chip.step()
        await ReadOnly()
        if self.monitor is not None:
            self.monitor.compare_one()
        await Timer(1, unit="ns")
        if wr and address == self.cmap.defs["TRW_HA_RUN"]:
            _apply_host_write(self.chip, self.cmap, address, value)

    async def cycles(self, count: int):
        for _ in range(count):
            await FallingEdge(self.d.clk)
            await self._one_from_falling()

    def _drive(self, bit, value):
        self.ui = (self.ui | (1 << bit)) if value else (self.ui & ~(1 << bit))
        self.d.ui_in.value = self.ui

    async def transfer(self, payload):
        await FallingEdge(self.d.clk)
        self._drive(CSN, 0)
        await self._one_from_falling()
        await self.cycles(4)
        reply = []
        for byte in payload:
            result = 0
            for bit in range(7, -1, -1):
                self._drive(MOSI, (byte >> bit) & 1)
                await self.cycles(4)
                result = (result << 1) | ((_bits(self.d.uo_out) >> MISO) & 1)
                self._drive(SCK, 1)
                await self.cycles(4)
                self._drive(SCK, 0)
            reply.append(result)
        await self.cycles(4)
        self._drive(CSN, 1)
        await self.cycles(8)
        return bytes(reply)

    async def write(self, address, words):
        await self.transfer(frame_write(address, list(words)))


def _bits(handle):
    value = handle.value
    return int(value) if value.is_resolvable else 0


def _drive_rx_bit(cycle: int) -> int:
    """Deterministic repeated 8N1 stream; holds idle high outside each 10-bit frame."""
    period, frame_bits = 8, 10
    phase = (cycle // period) % frame_bits
    frame_no = (cycle // (period * frame_bits)) & 3
    byte = (0xA6, 0x5A, 0x00, 0xFF)[frame_no]
    if phase == 0:
        return 0
    if 1 <= phase <= 8:
        return (byte >> (phase - 1)) & 1
    return 1


async def _boot(dut, chip: Chip, cmap: CandidateMap):
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())
    dut.ui_in.value = (1 << CSN) | 1
    dut.uio_in.value = 0xFF
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
    chip.cycle = _bits(dut.dbg_cycle)
    chip.settle_inputs(ui=(1 << CSN) | 1, uio=0xFF)
    return HostSPI(dut, chip, cmap)


async def _program_candidate(host: HostSPI, cmap: CandidateMap, words):
    defs = cmap.defs
    for lane in range(2):
        for index in range(12):
            word = words.get((lane, index), 0)
            address = defs["TRW_HA_SLOTS"] + (lane << 8) + (index << 4)
            await host.write(address, slot_words(word))
        # H1 requires the routine constants to be initialized before RUN too.
        await host.write(defs["TRW_HA_SLOTS"] + (lane << 8) + (12 << 4), [0, 0, 0, 0])
    for unit in range(4):
        cfg = PinConfig(**PIN_CONFIG) if unit == 0 else PinConfig()
        await host.write(defs["TRW_HA_PIN_CFG"] + unit * 32,
                         pinregs.encode(cfg, unit=unit))
    active_sources = {"L0.I0": "U0.rx"}
    for port in cmap.consumers:
        source = active_sources.get(port, cmap.legal_sources[port][0])
        await host.write(cmap.host_address("PORTS", port),
                         [cmap.port_word(port, source, enable=port in active_sources)])


def _stimulus(chip: Chip, cycle: int):
    ui0 = _drive_rx_bit(cycle)
    chip.ui_in = (1 << CSN) | ui0
    chip.uio_in = 0xFF


def _apply_host_write(chip: Chip, cmap: CandidateMap, address: int, value: int):
    port_base = cmap.defs["TRW_HA_PORTS"]
    if port_base <= address < port_base + len(cmap.consumers):
        index = address - port_base
        name = cmap.consumers[index]
        sel, tap = (value >> 2) & 15, (value >> 1) & 1
        source = cmap.legal_sources[name][sel] if sel < len(cmap.legal_sources[name]) else None
        port = chip.fabric.ports[name]
        if port.src is not None:
            port.src.subs.remove(port)
        port._take = False
        port.en, port.blocking, port.accept = value & 1, int(not tap), (value >> 6) & 15
        port.host_sel = sel
        port.src = chip.fabric.producers.get(source) if source is not None else None
        if port.src is not None:
            port.src.subs.append(port)
            port.last_seq = port.src.seq
        return
    if address == cmap.defs["TRW_HA_PIN_CFG"] or (
            cmap.defs["TRW_HA_PIN_CFG"] < address < cmap.defs["TRW_HA_PIN_CFG"] + 4 * 32):
        # Candidate counts are four units; Chip.host_write decodes the same base/stride.
        chip.host_write(address, value)
        return
    chip.host_write(address, value)


async def _clock_compare(dut, chip: Chip, cmap: CandidateMap, cycles: int, *, check=True):
    compared = 0
    first = None
    await FallingEdge(dut.clk)
    # The SPI helper ends on a falling-edge trigger, which may leave one
    # just-completed active clock after its return. Mirror any such idle-input
    # clocks before starting the counted comparison window.
    rtl_cycle = _bits(dut.dbg_cycle)
    gap = (rtl_cycle - chip.cycle) & 0xFFFF
    if gap > 32:
        raise AssertionError(f"unexpected RTL/model alignment gap: rtl={rtl_cycle}, model={chip.cycle}")
    if gap:
        chip.run_for(gap, lambda c: (setattr(c, "ui_in", (1 << CSN) | 1), setattr(c, "uio_in", 0xFF)))
    for index in range(cycles):
        if index:
            await FallingEdge(dut.clk)
        # Use the next model input cycle; pin stimulus is a deterministic function of absolute time.
        cycle = chip.cycle
        _stimulus(chip, cycle)
        dut.ui_in.value = (1 << CSN) | _drive_rx_bit(cycle)
        dut.uio_in.value = 0xFF
        await RisingEdge(dut.clk)
        await ReadOnly()
        chip.step()
        expected, observed = model_snapshot(chip), rtl_snapshot(dut, cmap)
        if check:
            # Cycle numbers are checked separately: the candidate tnow tap is
            # sampled at the post-edge boundary, while chip.cycle denotes the
            # count of edges already modelled.
            exp_state, obs_state = dict(expected), dict(observed)
            exp_cycle, obs_cycle = exp_state.pop("cycle"), obs_state.pop("cycle")
            mismatch = first_difference(exp_state, obs_state)
            if mismatch is None and exp_cycle != obs_cycle:
                mismatch = (("cycle", exp_cycle, obs_cycle),)
            if mismatch:
                first = (mismatch, expected.get("cycle"), observed.get("cycle"))
                lane = chip.lanes[0]
                in0 = chip.fabric.ports["L0.I0"]
                dut._log.warning("first L2 divergence at compared clock %d: %r; RTL/model cycle=%d/%d; "
                                 "model L0.I0 avail=%d seq=%d/%d, L0 fired=%s",
                                 compared, mismatch, observed["cycle"], expected["cycle"],
                                 in0.avail(), in0.last_seq, in0.src.seq, lane.stats["fired"][:2])
                dut._log.warning("lane0 debug model=%s RTL=%s; producers model=%s RTL=%s; ports model=%s RTL=%s",
                                 expected["lanes"][0]["debug"], observed["lanes"][0]["debug"],
                                 expected["producers"], observed["producers"],
                                 expected["ports"][:1], observed["ports"][:1])
                dut._log.warning("lane0 reflex slots RTL=(%013x,%013x), expected=(%013x,%013x)",
                                 _bits(dut.dbg_lane0_slots) & ((1 << 53) - 1),
                                 (_bits(dut.dbg_lane0_slots) >> 53) & ((1 << 53) - 1),
                                 slot(OP=S.OPS["MOV"], DST=S.DST["r0"], ASRC=S.ASRC["I0"], DQ=1),
                                 slot(OP=S.OPS["MOV"], DST=S.DST["r1"], ASRC=S.ASRC["I0"], DQ=1))
                break
        compared += 1
        if compared % 100_000 == 0:
            dut._log.info("L2 progress: %d/%d clocks compared", compared, cycles)
    return compared, first


class LockstepMonitor:
    """Compare one post-edge model/RTL snapshot during directed injection."""

    def __init__(self, dut, chip, cmap):
        self.dut, self.chip, self.cmap = dut, chip, cmap
        self.compared = 0

    def compare_one(self):
        expected, observed = model_snapshot(self.chip), rtl_snapshot(self.dut, self.cmap)
        exp_state, obs_state = dict(expected), dict(observed)
        exp_cycle, obs_cycle = exp_state.pop("cycle"), obs_state.pop("cycle")
        mismatch = first_difference(exp_state, obs_state)
        if mismatch is None and exp_cycle != obs_cycle:
            mismatch = (("cycle", exp_cycle, obs_cycle),)
        self.compared += 1
        if mismatch:
            self.dut._log.warning("first lockstep divergence during directed stimulus at clock %d: %r; "
                                  "RTL/model cycle=%d/%d", self.compared, mismatch,
                                  observed["cycle"], expected["cycle"])
            unit = self.chip.pins[0]
            self.dut._log.warning("cursor diagnostic: level=%d cursor_q8=%d actions=%s tx=%s",
                                  unit.level, unit.cursor_q8, unit.actions,
                                  (unit.tx_port.avail(), unit.tx_port.last_seq,
                                   unit.tx_port.src.seq if unit.tx_port.src else None))
            self.dut._log.warning("RTL U0 TX: level=%d cursor=(%d,%d) due=%d pin_a=%d",
                                  _bits(self.dut.dbg_u0_level), _bits(self.dut.dbg_u0_cursor_q),
                                  _bits(self.dut.dbg_u0_cursor_r), _bits(self.dut.dbg_u0_due_level),
                                  _bits(self.dut.dbg_u0_pin_a))
            raise AssertionError(f"first lockstep divergence at directed clock {self.compared}: {mismatch}")


async def _run_cursor_scenario(dut, cmap):
    """Deterministic LEVEL/GAP stream with a visible cursor boundary."""
    chip = Chip(lanes=2, pin_units=4, slots=12, sram_words=512)
    host = await _boot(dut, chip, cmap)
    # H1: initialise both lanes' slots and routine constants before RUN.
    for lane in range(2):
        for index in range(12):
            await host.write(cmap.defs["TRW_HA_SLOTS"] + (lane << 8) + (index << 4), [0, 0, 0, 0])
        await host.write(cmap.defs["TRW_HA_SLOTS"] + (lane << 8) + (12 << 4), [0, 0, 0, 0])
    # Every candidate unit receives a known configuration; U0 alone drives uo0.
    for unit in range(4):
        cfg = (PinConfig(pin_a=PAD_UO, txmode="level", rxmode="off", idle=0,
                         autorearm=True, period=8, presc=1, nbits=9, rx_nbits=10)
               if unit == 0 else PinConfig())
        await host.write(cmap.defs["TRW_HA_PIN_CFG"] + 32 * unit, pinregs.encode(cfg, unit=unit))
    for port in cmap.consumers:
        source = "HOST_IN" if port == "U0.tx" else cmap.legal_sources[port][0]
        await host.write(cmap.host_address("PORTS", port),
                         [cmap.port_word(port, source, enable=port == "U0.tx")])
    await host.write(cmap.host_address("OWNERS") + (PAD_UO - 8), [0])
    await host.write(cmap.host_address("RUN"), [1])

    # Match the SPI helper's return point to the last completed RTL edge.
    rtl_cycle = _bits(dut.dbg_cycle)
    gap = (rtl_cycle - chip.cycle) & 0xFFFF
    if gap > 32:
        raise AssertionError(f"unexpected cursor-scenario alignment gap: RTL={rtl_cycle}, model={chip.cycle}")
    if gap:
        chip.run_for(gap, lambda c: (setattr(c, "ui_in", 1 << CSN), setattr(c, "uio_in", 0xFF)))

    monitor = LockstepMonitor(dut, chip, cmap)
    host.monitor = monitor
    ctrl_base = cmap.host_address("HOST_IN") + S.TAGS["CTRL"]
    # P4/P32: a delayed LEVEL is relative to the persistent cursor and changes
    # the owned pad at the selected edge.
    await host.write(ctrl_base, [0x1800 | 500])  # LEVEL 1 after five hundred ticks
    await host.cycles(700)
    dut._log.info("L2-INJECT cursor scenario: compared %d clocks, zero divergences", monitor.compared)


@cocotb.test()
async def test_l2_lockstep(dut):
    """L2-RAND: deterministic legal pin stimulus and program compared on every clock."""
    cmap = CandidateMap(RTL_DIR)
    assert len(cmap.producers) == 9 and len(cmap.consumers) == 9, (cmap.producers, cmap.consumers)
    assert cmap.producers == ("U0.rx", "U1.rx", "U2.rx", "U3.rx", "L0.O0", "L0.O1", "L1.O0", "L1.O1", "HOST_IN")
    assert cmap.consumers == ("L0.I0", "L0.I1", "L1.I0", "L1.I1", "U0.tx", "U1.tx", "U2.tx", "U3.tx", "HOST_OUT")
    if os.environ.get("L2_SCENARIO") == "cursor":
        await _run_cursor_scenario(dut, cmap)
        return
    chip, words = make_setup()
    host = await _boot(dut, chip, cmap)
    await _program_candidate(host, cmap, words)
    expected_slots = (words[(0, 0)], words[(0, 1)])
    raw_slots = _bits(dut.dbg_lane0_slots)
    observed_slots = (raw_slots & ((1 << 53) - 1), (raw_slots >> 53) & ((1 << 53) - 1))
    dut._log.info("L2 loaded lane0 slots: RTL=%013x,%013x expected=%013x,%013x",
                  *observed_slots, *expected_slots)
    assert observed_slots == expected_slots, f"R4 host slot load mismatch: {observed_slots} != {expected_slots}"

    await host.transfer(frame_write(cmap.host_address("RUN"), [0b11]))
    dut._log.info("L2 alignment after setup: RTL=%d model=%d", _bits(dut.dbg_cycle), chip.cycle)

    cycles = int(os.environ.get("L2_CYCLES", "2048"))
    compared, mismatch = await _clock_compare(dut, chip, cmap, cycles)
    assert mismatch is None, f"first lockstep divergence after {compared} clocks: {mismatch}"
    dut._log.info("L2 candidate %s: compared %d clocks, zero divergences", RTL_REV, compared)

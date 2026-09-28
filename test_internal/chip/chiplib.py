"""Chip-level test library: drive trw_chip through its pins only.

- `Pins`: an SPI controller on the host pins that speaks tools/host frames (SCK = clk/8, the §9 limit).
- `start` / `load`: reset, and load a tripc image with tools/host.load_sequence (§14 H1).
- `push` / `pop`: HOST_IN with its busy check, HOST_OUT.
- `Wire`: a per-clock environment on the protocol pads (a reference model steps once per clock) that
  records named pad levels; `write_vcd` / `sigrok` turn the record into an independent decode.
"""

import pathlib
import re
import shutil
import subprocess
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, ReadOnly, RisingEdge

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import tripc  # noqa: E402,F401
import tripwire_spec as S  # noqa: E402
from host import HM, frame_read, frame_write, load_sequence  # noqa: E402

H = 4                                         # SCK half period (clk/8)
CSN, SCK, MOSI, MISO = 4, 5, 6, 3
TAGS = S.TAGS


class Pins:
    """An SPI controller on the chip's host pins, speaking tools/host frames. Also owns the other ui pins
    (`set_ui`), so a protocol environment and the host can share ui_in."""

    def __init__(self, dut):
        self.d = dut
        self.ui = 1 << CSN
        self.outq = []
        dut.ui_drv.value = self.ui

    def set_ui(self, bit, v):
        self.ui = (self.ui | 1 << bit) if v else (self.ui & ~(1 << bit))
        self.d.ui_drv.value = self.ui

    async def xfer(self, data):
        d = self.d
        await FallingEdge(d.clk)
        self.set_ui(CSN, 0)
        await ClockCycles(d.clk, H, rising=False)
        reply = []
        for byte in data:
            r = 0
            for i in range(7, -1, -1):
                self.set_ui(MOSI, byte >> i & 1)
                await ClockCycles(d.clk, H, rising=False)
                v = d.uo_out.value
                assert v.is_resolvable, f"uo_out has X/Z: {v}"
                r = r << 1 | (int(v) >> MISO & 1)
                self.set_ui(SCK, 1)
                await ClockCycles(d.clk, H, rising=False)
                self.set_ui(SCK, 0)
            reply.append(r)
        await ClockCycles(d.clk, H, rising=False)
        self.set_ui(CSN, 1)
        await ClockCycles(d.clk, 2 * H, rising=False)
        return bytes(reply)

    async def write(self, addr, words):
        await self.xfer(frame_write(addr, list(words)))

    async def read(self, addr, n=1):
        out, parse = frame_read(addr, n)
        return parse(await self.xfer(out))

    async def poll(self):
        """One transaction: status, then data. A HOST_OUT token is taken (only when the data word has been
        shifted out, and only if there was one: D-046, BUGS #47) and queued in `outq`. Returns the status."""
        st, data = await self.read(HM["host_status"], 2)
        if st >> 15:
            self.outq.append((st & 3, data))
        return st

    async def push(self, data, tag=TAGS["DATA"], tries=2000):
        """HOST_IN push once it is free (a push while busy is refused, D-046). HOST_OUT is drained while
        waiting: its port is blocking, so a program that answers each command stalls until the host reads."""
        for _ in range(tries):
            if await self.poll() >> 14 & 1:
                await self.write(HM["host_in"] + tag, [data])
                return
        raise AssertionError("HOST_IN never became free")

    async def pop(self):
        """(tag, data) from HOST_OUT (queued first), or None."""
        if not self.outq:
            await self.poll()
        return self.outq.pop(0) if self.outq else None


async def start(dut, ui=0, uio=0, clock=True):
    """Clock (once per test: pass clock=False on later calls), reset with the pads held at `ui` / `uio`,
    returns Pins."""
    if clock:
        cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())
    dut.ena.value, dut.loop0.value, dut.uio_in.value = 1, 0, uio
    p = Pins(dut)
    for b in range(8):
        if b not in (CSN, SCK, MOSI) and ui >> b & 1:
            p.set_ui(b, 1)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
    return p


async def load(p, program, run=True, **params):
    image, _ = tripc.compile_file(ROOT / "programs" / f"{program}.trw", params or None)
    for addr, words in load_sequence(image, run):
        await p.write(addr, words)
    return image


class Wire:
    """A per-clock pad environment. `fn(uo, uio_out, uio_oe, uio_bus)` is called once per clock with this
    clock's chip outputs and returns (ui_bits: {bit: level}, uio_ext: {bit: level released=1}) to apply
    from the next clock. uio pads are open drain on the bus: level = AND of the chip (drives only when
    its OE is 1) and the environment. Named pad levels are recorded every clock."""

    def __init__(self, p, fn, probes):
        self.p, self.fn, self.probes = p, fn, probes
        self.rec = {name: [] for name in probes}
        self.uio_ext = 0xFF
        self.clocks = 0
        self._task = cocotb.start_soon(self._run())

    def bus(self, uio_out, uio_oe):
        chip = (~uio_oe | uio_out) & 0xFF                # chip releases where OE = 0
        return chip & self.uio_ext

    async def _run(self):
        d = self.p.d
        while True:
            await RisingEdge(d.clk)
            await ReadOnly()
            uo = int(d.uo_out.value)
            uout, uoe = int(d.uio_out.value), int(d.uio_oe.value)
            bus = self.bus(uout, uoe)
            for name, f in self.probes.items():
                self.rec[name].append(f(uo, bus))
            ui_bits, uio_ext = self.fn(uo, uout, uoe, bus)
            await FallingEdge(d.clk)
            for b, v in ui_bits.items():
                self.p.set_ui(b, v)
            if uio_ext is not None:
                for b, v in uio_ext.items():
                    self.uio_ext = (self.uio_ext | 1 << b) if v else (self.uio_ext & ~(1 << b))
            d.uio_in.value = self.bus(int(d.uio_out.value), int(d.uio_oe.value))
            self.clocks += 1

    def stop(self):
        self._task.cancel()


def write_vcd(path, rec):
    """A VCD of recorded pad levels, one sample per 50 MHz clock (20 ns)."""
    names = list(rec)
    ids = {n: chr(33 + i) for i, n in enumerate(names)}
    lines = ["$timescale 20 ns $end", "$scope module chip $end"]
    lines += [f"$var wire 1 {ids[n]} {n} $end" for n in names]
    lines += ["$upscope $end", "$enddefinitions $end"]
    prev = {}
    for t in range(max(len(v) for v in rec.values())):
        ch = [f"{rec[n][t]}{ids[n]}" for n in names if t < len(rec[n]) and prev.get(n) != rec[n][t]]
        if ch or t == 0:
            lines.append(f"#{t}")
            lines += ch
            for n in names:
                if t < len(rec[n]):
                    prev[n] = rec[n][t]
    lines.append(f"#{max(len(v) for v in rec.values())}")
    pathlib.Path(path).write_text("\n".join(lines) + "\n")


def sigrok(vcd, decoder, annotation=None):
    """sigrok-cli's decode of a VCD (stdout); None if sigrok-cli is not installed."""
    if shutil.which("sigrok-cli") is None:
        return None
    cmd = ["sigrok-cli", "-i", str(vcd), "-I", "vcd", "-P", decoder]
    if annotation:
        cmd += ["-A", annotation]
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def hex_bytes(text, prefix):
    return [int(h, 16) for h in re.findall(rf"{prefix}([0-9A-F]{{2}})\b", text)]

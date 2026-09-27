# SPDX-FileCopyrightText: © 2026 Kanishk Sama
# SPDX-License-Identifier: Apache-2.0
#
# cocotb side of the WARP host: drives the host SPI pins (ARCHITECTURE.md §2) with transactions
# built by tools/host/protocol.py, the same API board software uses. Top-level ports only.

import sys
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from host.protocol import (ARCH_VERSION, ErrorCode, Op, load_transactions,  # noqa: E402
                           parse_read_status, parse_status, tx_read_status, tx_simple)

CS_N, SCK, MOSI = 0, 1, 2
HALF = 4        # clk cycles per SCK phase: SCK = clk/8, the fastest the spec allows
CS_SETUP = 8    # clk cycles from CS_N falling to the first SCK rising edge
CS_IDLE = 4     # clk cycles CS_N stays high between transactions


def bit(signal, i):
    """One bit of a bus. A black-box fabric drives X on the fabric pins while RUNNING, so the
    host pins are read bit by bit rather than as a whole integer."""
    return int(str(signal.value)[-1 - i])


class Host:
    """Drives the host SPI pins (mode 0) and returns the MISO bytes of each transaction.
    `fab_in` holds the value of FAB_IN0..4 (ui[3..7]), kept while the SPI pins toggle."""

    def __init__(self, dut):
        self.dut = dut
        self.fab_in = 0
        self._spi = 1 << CS_N
        self._drive()

    def _drive(self):
        self.dut.ui_in.value = (self.fab_in & 0x1F) << 3 | self._spi

    @property
    def ui(self):
        return (self.fab_in & 0x1F) << 3 | self._spi

    def set_fab_in(self, value):
        self.fab_in = value
        self._drive()

    def _pins(self, cs_n, sck, mosi):
        self._spi = (cs_n << CS_N) | (sck << SCK) | (mosi << MOSI)
        self._drive()

    async def xfer(self, mosi_bytes, abort_after_bits=None):
        clk = self.dut.clk
        self._pins(0, 0, 0)
        await ClockCycles(clk, CS_SETUP)
        miso, nbits = [], 0
        for b in mosi_bytes:
            r = 0
            for i in range(7, -1, -1):
                if abort_after_bits is not None and nbits == abort_after_bits:
                    break
                self._pins(0, 0, (b >> i) & 1)
                await ClockCycles(clk, HALF)
                r = (r << 1) | bit(self.dut.uo_out, 0)   # sampled at the rising edge
                self._pins(0, 1, (b >> i) & 1)
                await ClockCycles(clk, HALF)
                nbits += 1
            miso.append(r)
        self._pins(0, 0, 0)
        await ClockCycles(clk, HALF)
        self._pins(1, 0, 0)
        await ClockCycles(clk, CS_IDLE)
        return miso

    async def status(self):
        return parse_status(await self.xfer(tx_simple(Op.READ_ID)))

    async def read_status(self):
        return parse_read_status(await self.xfer(tx_read_status()))

    async def load(self, words, arch_version=ARCH_VERSION, chunk=5):
        for t in load_transactions(words, chunk, arch_version):
            await self.xfer(t)


async def reset(dut):
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())
    dut.ena.value = 1
    dut.uio_in.value = 0
    host = Host(dut)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
    return host


def parked(dut):
    return ((int(dut.uo_out.value) >> 2) == 0 and int(dut.uio_oe.value) == 0
            and int(dut.uio_out.value) == 0)


def irq(dut):
    return bit(dut.uo_out, 1)


async def expect(host, state, code=ErrorCode.NONE):
    st, err = await host.read_status()
    assert st.state == state, f"state {st.state!r}, expected {state!r} (error {err!r})"
    assert err == code, f"error code {err!r}, expected {code!r}"
    assert st.error_pending == (code != ErrorCode.NONE)

# SPDX-FileCopyrightText: © 2024 Tiny Tapeout, 2026 Kanishk Sama
# SPDX-License-Identifier: Apache-2.0
#
# Pin-level tests of the WARP shell (ARCHITECTURE.md §1–4) through the host SPI interface, using
# the host software in tools/host (the same API boards will use). Top-level ports only, so the
# suite also runs on the gate-level netlist. These tests only rely on the shell: bitstreams are
# synthetic but well-formed (sync word, frames, desync), and whatever the fabric model is, the
# fabric pins are only checked while parked. Real compiled bitstreams: test_bitstream.py.

import cocotb
from cocotb.triggers import ClockCycles

import re
from pathlib import Path

from warp_host import expect, irq, parked, reset
from compile.bitfile import BitFile
from host.protocol import (ARCH_VERSION, SYNC_WORD, ErrorCode, Op, State, crc32_words,
                           parse_byte, parse_read_id, parse_status, tx_ch_write, tx_load_begin,
                           tx_load_data, tx_load_end, tx_read_id, tx_simple, tx_user_status)


ROOT = Path(__file__).resolve().parents[1]
# configuration rows of the current fabric (arch.yaml; no YAML package in the CI test jobs)
ROWS = int(re.search(r"^config_rows:\s*(\d+)", (ROOT / "arch" / (ROOT / "arch/CURRENT").read_text()
                                                .strip() / "arch.yaml").read_text(), re.M).group(1))


def idle():
    """The compiled `idle` design (tools/compile/examples): every host-channel output 0. Tests
    that RUN load it, so the shell sees defined values from whatever fabric model is simulated
    (an unconfigured fabric's outputs are arbitrary)."""
    return BitFile.load(Path(__file__).resolve().parent / "bitstreams" / "idle.wbit").words


def bitstream(frames=2, rows=ROWS):
    """A well-formed FABulous frame bitstream: sync word, per frame a header and one data word per
    row, then the desync header (bit 20). Data words are 0 (all-default configuration), so that
    with a real fabric model (RTL or gate level) no random routing loop is configured."""
    words = [SYNC_WORD]
    for f in range(frames):
        words.append((f % 3) << 27 | 1 << f)            # column select | frame strobe bit
        words += [0] * rows
    words.append(1 << 20)
    return words


@cocotb.test()
async def test_reset_state(dut):
    host = await reset(dut)
    assert parked(dut)
    assert int(dut.uo_out.value) & 0b11 == 0, "MISO 0 while CS_N high, no IRQ"
    await expect(host, State.UNCONFIGURED)


@cocotb.test()
async def test_read_id(dut):
    host = await reset(dut)
    miso = await host.xfer(tx_read_id())
    assert parse_status(miso).state == State.UNCONFIGURED
    assert parse_read_id(miso) == (True, ARCH_VERSION)


@cocotb.test()
async def test_load_run_stop(dut):
    host = await reset(dut)
    await host.load(idle())
    await expect(host, State.LOADED)
    assert parked(dut)
    await host.xfer(tx_simple(Op.RUN))
    await expect(host, State.RUNNING)
    await host.xfer(tx_simple(Op.STOP))
    await expect(host, State.LOADED)
    assert parked(dut)
    await host.xfer(tx_simple(Op.RUN))           # a loaded design can be restarted
    await expect(host, State.RUNNING)


@cocotb.test()
async def test_wrong_arch_version(dut):
    host = await reset(dut)
    await host.xfer(tx_load_begin(4, ARCH_VERSION + 1))
    assert irq(dut), "IRQ in ERROR"
    await expect(host, State.ERROR, ErrorCode.WRONG_ARCH)
    await expect(host, State.ERROR)             # READ_STATUS cleared the code, state stays
    await host.xfer(tx_simple(Op.RUN))
    await expect(host, State.ERROR, ErrorCode.BAD_COMMAND)
    assert parked(dut)
    await host.load(idle())                     # a correct load recovers
    await expect(host, State.LOADED)
    assert not irq(dut)


@cocotb.test()
async def test_bad_crc(dut):
    host = await reset(dut)
    words = bitstream()
    await host.xfer(tx_load_begin(len(words)))
    await host.xfer(tx_load_data(words))
    await host.xfer(tx_load_end(crc32_words(words) ^ 1))
    await expect(host, State.ERROR, ErrorCode.CRC)
    await host.xfer(tx_simple(Op.RUN))
    await expect(host, State.ERROR, ErrorCode.BAD_COMMAND)
    assert parked(dut)


@cocotb.test()
async def test_length_mismatch(dut):
    host = await reset(dut)
    words = bitstream()
    for n in (len(words) - 1, len(words) + 1):  # fewer and more words than announced
        await host.xfer(tx_load_begin(n))
        await host.xfer(tx_load_data(words))
        await host.xfer(tx_load_end(crc32_words(words)))
        await expect(host, State.ERROR, ErrorCode.LENGTH)


@cocotb.test()
async def test_bad_sync_word(dut):
    host = await reset(dut)
    words = [0xDEAD_BEEF] + bitstream()[1:]
    await host.load(words)
    await expect(host, State.ERROR, ErrorCode.FORMAT)


@cocotb.test()
async def test_empty_load_rejected(dut):
    """BUGS #12: a zero-length load has no sync word; it must not reach LOADED."""
    host = await reset(dut)
    await host.xfer(tx_load_begin(0))
    await host.xfer(tx_load_end(crc32_words([])))
    await expect(host, State.ERROR, ErrorCode.FORMAT)


@cocotb.test()
async def test_bad_commands_change_nothing(dut):
    host = await reset(dut)
    for op in (Op.RUN, Op.STOP, Op.LOAD_DATA, 0x7F):
        await host.xfer([op])
        await expect(host, State.UNCONFIGURED, ErrorCode.BAD_COMMAND)
    await host.load(idle())
    await host.xfer(tx_simple(Op.RUN))
    await host.xfer(tx_load_begin(4))           # never starts a load while running
    await expect(host, State.RUNNING, ErrorCode.BAD_COMMAND)


@cocotb.test()
async def test_aborted_transaction_keeps_whole_words(dut):
    host = await reset(dut)
    words = bitstream()
    await host.xfer(tx_load_begin(len(words)))
    # first 3 words, then 2 bytes + 3 bits of the 4th: CS_N rises mid-word
    await host.xfer(tx_load_data(words[:4]), abort_after_bits=8 + 3 * 32 + 19)
    await host.xfer(tx_load_data(words[3:]))
    await host.xfer(tx_load_end(crc32_words(words)))
    await expect(host, State.LOADED)


@cocotb.test()
async def test_reload_from_loaded(dut):
    host = await reset(dut)
    await host.load(bitstream(frames=1))
    await host.load(bitstream(frames=3))
    await expect(host, State.LOADED)
    await host.xfer(tx_load_begin(3))           # start a load, then restart it
    await host.load(bitstream())
    await expect(host, State.LOADED)


@cocotb.test()
async def test_host_channel_overflow(dut):
    """The current fabric never takes channel bytes, so the 2-entry FIFO fills and the third write
    overflows (ch_overflow sticky until READ_STATUS)."""
    host = await reset(dut)
    await host.load(idle())
    await host.xfer(tx_simple(Op.RUN))
    st = await host.status()
    assert st.tx_ready and not st.rx_valid and not st.ch_overflow
    await host.xfer(tx_ch_write(0x11))
    await host.xfer(tx_ch_write(0x22, last=True))
    st = await host.status()
    assert not st.tx_ready and not st.ch_overflow
    await host.xfer(tx_ch_write(0x33))
    st, _ = await host.read_status()
    assert st.ch_overflow
    st, _ = await host.read_status()
    assert not st.ch_overflow
    assert parse_byte(await host.xfer(tx_user_status())) == 0
    await host.xfer(tx_simple(Op.STOP))         # stopping empties the channels
    await host.xfer(tx_simple(Op.RUN))
    assert (await host.status()).tx_ready


@cocotb.test()
async def test_user_inputs_do_not_affect_parking(dut):
    host = await reset(dut)
    await host.load(bitstream())
    for v in (0x00, 0xFF, 0xA5):
        dut.uio_in.value = v
        host.set_fab_in(0x1F)
        await ClockCycles(dut.clk, 10)
        assert parked(dut)

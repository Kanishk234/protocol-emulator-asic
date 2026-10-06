"""Queue boundary contract through user-design top ports, no internal state."""
import os
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, ReadOnly, Timer


@cocotb.test()
async def full_pop_accepts_event(dut):
    tick = 1 << int(os.environ["STAMP_SHIFT"])
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())
    dut.rst_n.value = 0
    dut.rx_i.value = 1
    dut.event_i.value = 0
    dut.capture_select_i.value = 1
    dut.h_wdata.value = 0
    dut.h_wvalid.value = 0
    dut.h_rready.value = 0

    async def cycle(**pins):
        await FallingEdge(dut.clk)
        for name, value in pins.items():
            getattr(dut, name).value = value
        await RisingEdge(dut.clk)
        await ReadOnly()
        result = (int(dut.h_rdata.value), int(dut.h_rvalid.value),
                  int(dut.h_status.value) & 0xE0)
        await Timer(1, unit="ns")
        return result

    await cycle()
    await cycle(rst_n=1)
    await cycle(event_i=1)
    first, valid, status = await cycle(event_i=0)
    assert valid and status == 0x20
    for _ in range(6):
        await cycle()
    await cycle(event_i=1)
    head, valid, status = await cycle(event_i=0)
    assert (head, valid, status) == (first, 1, 0x60)
    for _ in range(6):
        await cycle()
    await cycle(event_i=1)
    # The delayed rising event and ready are sampled on this same clock.
    second, valid, status = await cycle(event_i=0, h_rready=1)
    assert valid and status == 0x60, "full pop/push must keep two entries without overflow"
    assert (second-first) % 64 == 8 // tick
    third, valid, status = await cycle()
    assert valid and status == 0x20
    assert (third-second) % 64 == 8 // tick
    _, valid, status = await cycle()
    assert not valid and status == 0

    # An empty ready queue must retain a newly detected event for the next cycle.
    await cycle(event_i=1)
    _, valid, status = await cycle(event_i=0)
    assert valid and status == 0x20
    _, valid, status = await cycle()
    assert not valid and status == 0

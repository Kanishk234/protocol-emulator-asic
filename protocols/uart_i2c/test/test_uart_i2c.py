"""Concurrent pin traffic checked against the existing independent I2C target."""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer, with_timeout
from refmodels.i2c import Target, decode, wired_and
from test_uart_spi import cycle, put, get, uart_peer

@cocotb.test()
async def concurrent_i2c_uart(d):
    cocotb.start_soon(Clock(d.clk, 10, unit='ns').start())
    d.rst_n.value = 0
    d.rx_i.value = 1
    d.sda_i.value = 1
    d.scl_i.value = 1
    d.h_wdata.value = 0
    d.h_wvalid.value = 0
    d.h_rready.value = 0
    await cycle(d, 5)
    d.rst_n.value = 1
    target = Target(0x42, stretch=7)
    samples = [[], []]
    async def bus():
        drive = (1, 1)
        while True:
            await RisingEdge(d.clk)
            sda = wired_and(1-int(d.sda_oe.value), drive[0])
            scl = wired_and(1-int(d.scl_oe.value), drive[1])
            samples[0].append(sda)
            samples[1].append(scl)
            drive = target.step(sda, scl)
            d.sda_i.value = sda
            d.scl_i.value = scl
    bus_task = cocotb.start_soon(bus())
    await cycle(d, 4)
    peer = cocotb.start_soon(uart_peer(d, [0x69], [0xa5]))
    await put(d, 0)
    await put(d, 0xa5)
    uart_received = []
    async def command(byte):
        await put(d, 1)
        await put(d, byte)
    async def reply():
        for _ in range(3):
            tag, value = await get(d), await get(d)
            if tag == 0:
                uart_received.append(value)
            else:
                assert tag == 1
                return value
        raise AssertionError('No I2C response')
    await command(0x00)  # START
    for byte in (0x84, 2, 0x5a):
        await command(0x40)
        await command(byte)
        assert await reply() == 0
    # Repeated START: set pointer, then another repeated START reads it.
    await command(0x00)
    for byte in (0x84, 2):
        await command(0x40)
        await command(byte)
        assert await reply() == 0
    await command(0x00)
    await command(0x40)
    await command(0x85)
    assert await reply() == 0
    await command(0x81)  # READ, NACK final byte
    assert await reply() == 0x5a
    await command(0xc0)
    if not uart_received:
        assert await get(d) == 0
        uart_received.append(await get(d))
    assert uart_received == [0x69]
    await with_timeout(peer, 100, 'us')
    await cycle(d, 100)
    assert target.regs[2] == 0x5a
    assert samples[0][-1] == samples[1][-1] == 1
    assert int(d.h_status.value) & 0xcf == 0
    events = decode(*samples)
    assert sum(e.kind == 'restart' for e in events) == 2
    assert any(e.kind == 'stop' for e in events)
    bus_task.cancel()

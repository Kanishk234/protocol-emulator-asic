"""Pin-level concurrent traffic and framed host backpressure checks."""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer, with_timeout

async def cycle(d, count=1):
    for _ in range(count):
        await RisingEdge(d.clk)
        await Timer(1, unit='ns')

async def put(d, byte):
    d.h_wdata.value = byte
    d.h_wvalid.value = 1
    for _ in range(4000):
        await Timer(1, unit='ns')
        ready = int(d.h_wready.value)
        await cycle(d)
        if ready:
            d.h_wvalid.value = 0
            return
    raise AssertionError('host write timeout')

async def get(d):
    d.h_rready.value = 0
    for _ in range(4000):
        if int(d.h_rvalid.value):
            value = int(d.h_rdata.value)
            # Valid data must remain stable while stalled.
            await cycle(d, 7)
            assert int(d.h_rvalid.value) and int(d.h_rdata.value) == value
            d.h_rready.value = 1
            await cycle(d)
            d.h_rready.value = 0
            return value
        await cycle(d)
    raise AssertionError('host read timeout')

async def uart_peer(d, sent, expected):
    async def receive():
        for value in expected:
            for _ in range(4000):
                if not int(d.tx_o.value):
                    break
                await cycle(d)
            else:
                raise AssertionError('UART start timeout')
            await cycle(d, 24)
            actual = 0
            for bit in range(8):
                actual |= int(d.tx_o.value) << bit
                await cycle(d, 16)
            assert actual == value
            assert int(d.tx_o.value) == 1
    task = cocotb.start_soon(receive())
    await cycle(d, 12)
    for byte in sent:
        d.rx_i.value = 0
        await cycle(d, 16)
        for bit in range(8):
            d.rx_i.value = (byte >> bit) & 1
            await cycle(d, 16)
        d.rx_i.value = 1
        await cycle(d, 32)
    await task

@cocotb.test()
async def concurrent_traffic(d):
    cocotb.start_soon(Clock(d.clk, 10, unit='ns').start())
    d.rst_n.value = 0
    d.rx_i.value = 1
    d.miso_i.value = 1
    d.h_wvalid.value = 0
    d.h_wdata.value = 0
    d.h_rready.value = 0
    await cycle(d, 4)
    d.rst_n.value = 1
    await cycle(d, 4)
    # Constant-one SPI target independently predicts 0xff in every mode.
    peer = cocotb.start_soon(uart_peer(d, [0x69], [0xa5]))
    await put(d, 0)
    await put(d, 0xa5)
    await put(d, 3)
    await put(d, 0x3c)
    # SPI finishes first; its stalled tag must survive UART becoming ready.
    await cycle(d, 80)
    assert int(d.h_rvalid.value) and int(d.h_rdata.value) == 1
    await cycle(d, 120)
    assert int(d.h_rvalid.value) and int(d.h_rdata.value) == 1
    packets = {}
    for _ in range(2):
        tag = await get(d)
        byte = await get(d)
        assert tag not in packets
        packets[tag] = byte
    assert packets == {0: 0x69, 1: 0xff}
    await with_timeout(peer, 100, 'us')
    await cycle(d, 20)
    assert int(d.cs_n_o.value) == 1
    assert int(d.h_status.value) & 0xd0 == 0
    # Reset discards an incomplete command header and response framing.
    await put(d, 3)
    d.rst_n.value = 0
    await cycle(d, 3)
    d.rst_n.value = 1
    await cycle(d, 3)
    await put(d, 3)
    await put(d, 0x81)
    assert await get(d) == 1
    assert await get(d) == 0xff

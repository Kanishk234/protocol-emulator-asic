"""Public TT-pin acceptance test, shared by RTL and post-layout gate simulation."""
import zlib
import cocotb
from cocotb.triggers import Timer
from small_counter_image import IMAGE

@cocotb.test()
async def test_project(dut):
    dut.clk.value = 0
    dut.ena.value = 1
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    async def step(pins=0, data=0):
        dut.clk.value = 0
        dut.uio_in.value = pins
        dut.ui_in.value = data
        await Timer(500, unit="ns")
        dut.clk.value = 1
        await Timer(500, unit="ns")

    def parked():
        assert int(dut.uio_oe.value) == 0, "unconfigured output enable"
        assert int(dut.uio_out.value) == 0, "unconfigured output data"

    async def send(value):
        for _ in range(30):
            if int(dut.uo_out.value) & 1:
                break
            await step()
        else:
            assert False, "host readiness timeout"
        await step(0x10, value)
        parked()
        await step()

    async def load(payload=IMAGE, crc=None):
        await step(0x20)
        parked()
        await step()
        checksum = zlib.crc32(payload) if crc is None else crc
        for value in checksum.to_bytes(4, "big") + payload:
            await send(value)
        for _ in range(12):
            await step()
            parked()

    async def commit(success):
        for _ in range(16):
            await step(0x40)
        if success:
            assert int(dut.uo_out.value) & 2, "valid image did not start"
            assert int(dut.uio_oe.value) == 12
        else:
            assert not (int(dut.uo_out.value) & 2)
            parked()

    async def count():
        expected = 0
        for index in range(128):
            reset = index % 31 == 0
            enable = index % 7 != 0
            expected = 0 if reset else ((expected + int(enable)) & 3)
            await step(int(reset) | (int(enable) << 1))
            assert int(dut.uio_oe.value) == 12
            assert (int(dut.uio_out.value) >> 2) & 3 == expected

    for _ in range(5):
        await step()
    parked()
    dut.rst_n.value = 1
    await step()
    await commit(False)
    await load()
    await commit(True)
    await count()
    # An incomplete replacement must park and cannot be committed.
    await load(IMAGE[:40], zlib.crc32(IMAGE))
    await commit(False)
    await step(0x80)
    parked()
    # Wrong CRC must not publish a complete image.
    await load(IMAGE, zlib.crc32(IMAGE) ^ 1)
    assert int(dut.uo_out.value) & 4
    await commit(False)
    # Recovery loads the real image into the same DUT.
    await load()
    await commit(True)
    await count()
    dut.ena.value = 0
    await step()
    parked()
    dut._log.info("PASS: TT pins load, execute, reject incomplete/CRC, recover, deselect")

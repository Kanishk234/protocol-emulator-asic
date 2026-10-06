"""Check the scratch CRC against zlib and the baseline, including mid-word clears."""
import random
import zlib
import cocotb
from cocotb.triggers import Timer


async def tick(dut):
    dut.clk.value = 0
    await Timer(10, unit="ns")
    dut.clk.value = 1
    await Timer(10, unit="ns")
    assert dut.crc.value == dut.baseline_crc.value
    assert dut.busy.value == dut.baseline_busy.value


@cocotb.test()
async def crc_matches_stable_word_stream(dut):
    rng = random.Random(0x57415250)
    dut.clk.value = 0
    dut.rst_n.value = 0
    dut.clear.value = 0
    dut.word_valid.value = 0
    dut.word.value = 0
    await tick(dut)
    dut.rst_n.value = 1
    for stream in range(40):
        dut.clear.value = 1
        await tick(dut)
        dut.clear.value = 0
        expected = 0
        words = [0, 0xFFFFFFFF, 0xFAB0FAB1, 0x01020304]
        words += [rng.getrandbits(32) for _ in range(rng.randrange(1, 30))]
        for word in words:
            dut.word.value = word
            dut.word_valid.value = 1
            await tick(dut)
            dut.word_valid.value = 0
            assert int(dut.busy.value) == 1
            for cycle in range(32):
                await tick(dut)
                assert int(dut.busy.value) == (cycle != 31)
            expected = zlib.crc32(word.to_bytes(4, "big"), expected)
            assert int(dut.crc.value) == expected
            # Outside busy, word may change freely without affecting the CRC.
            dut.word.value = rng.getrandbits(32)
            await tick(dut)
            assert int(dut.crc.value) == expected
        # Abort during an arbitrary bit; clear must discard partial work.
        dut.word_valid.value = 1
        await tick(dut)
        dut.word_valid.value = 0
        for _ in range(rng.randrange(1, 32)):
            await tick(dut)
        dut.clear.value = 1
        await tick(dut)
        assert int(dut.crc.value) == 0 and int(dut.busy.value) == 0

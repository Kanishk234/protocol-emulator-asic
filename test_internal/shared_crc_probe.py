"""Verify the scratch shared-word CRC's input-stability precondition in the shell."""
from cocotb.triggers import RisingEdge, Timer


async def monitor_word_stability(dut, stats):
    shell = dut.user_project.u_shell
    previous_busy = False
    previous_word = None
    while True:
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        word = str(shell.cfg_word.value)
        if previous_busy and int(shell.rst_n.value) and not int(shell.crc_clear.value):
            assert word == previous_word, "cfg_word changed while CRC was consuming it"
            stats["checked_cycles"] += 1
        previous_word = word
        previous_busy = bool(int(shell.crc_busy.value))

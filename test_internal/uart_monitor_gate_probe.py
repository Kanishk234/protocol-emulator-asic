"""Optional read-only white-box tracing for the UART/monitor gate-shell test."""
from cocotb.triggers import ClockCycles, ReadOnly, Timer


async def trace_monitor(dut, stop):
    previous = None
    while not stop[0]:
        await ClockCycles(dut.clk, 1)
        await ReadOnly()
        top = dut.user_project
        values = tuple(str(getattr(top, name).value) for name in
                       ("fab_in", "h_status", "cell_en"))
        tile = top.u_fabric.Tile_X3Y1_LUT4x8_ha
        values += tuple(str(getattr(tile, name).value) for name in
                        ("LG_I0", "LG_SR", "LG_EN", "LG_CLK", "LG_O"))
        values += tuple(str(getattr(tile, name).value) for name in
                        ("LB_EN", "LB_CLK", "LB_O"))
        if values != previous:
            dut._log.info("MONITOR_PROBE fab_in=%s h_status=%s cell_en=%s "
                          "event_prev_D=%s SR=%s EN=%s CLK=%s Q=%s "
                          "count_EN=%s count_CLK=%s count_Q=%s", *values)
            previous = values
        await Timer(1, "ns")

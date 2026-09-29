// L2 test adapter. Exposes candidate hierarchy taps so the Python scoreboard
// can compare logical lanes, producers, and consumers without using host-map
// offsets for the frozen 3-lane/6-unit configuration.
`default_nettype none
`timescale 1ns / 1ps

module tb_l2 (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [7:0] ui_in,
    input  wire [7:0] uio_in,
    output wire [7:0] uo_out,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    output wire [15:0] dbg_cycle,
    output wire [1:0] dbg_run,
    output wire dbg_live,
    output wire [359:0] dbg_lane,
    output wire [8:0] dbg_p_valid,
    output wire [8:0] dbg_p_seq,
    output wire [161:0] dbg_p_tok,
    output wire [89:0] dbg_port_state,
    output wire [71:0] dbg_dropped,
    output wire [3:0] dbg_overrun,
    output wire [3:0] dbg_late,
    output wire dbg_host_wr,
    output wire [15:0] dbg_host_wa,
    output wire [15:0] dbg_host_wd,
    output wire dbg_u0_level,
    output wire [15:0] dbg_u0_cursor_q,
    output wire [7:0] dbg_u0_cursor_r,
    output wire dbg_u0_due_level,
    output wire [4:0] dbg_u0_pin_a,
    output wire [105:0] dbg_lane0_slots
);
    tt_um_tripwire dut (
        .ui_in (ui_in), .uo_out (uo_out), .uio_in (uio_in),
        .uio_out (uio_out), .uio_oe (uio_oe), .ena (1'b1),
        .clk (clk), .rst_n (rst_n)
    );

    // Candidate R4 hierarchy: tt_um_tripwire.u_chip is trw_chip.
    assign dbg_cycle      = dut.u_chip.tnow;
    assign dbg_run        = dut.u_chip.run;
    assign dbg_live       = dut.u_chip.live;
    assign dbg_lane       = dut.u_chip.lane_dbg;
    assign dbg_p_valid    = dut.u_chip.p_valid;
    assign dbg_p_seq      = dut.u_chip.p_seq;
    assign dbg_p_tok      = dut.u_chip.p_tok;
    assign dbg_port_state = dut.u_chip.port_state;
    assign dbg_dropped    = dut.u_chip.dropped;
    assign dbg_overrun    = dut.u_chip.overrun;
    assign dbg_late       = dut.u_chip.late;
    assign dbg_host_wr    = dut.u_chip.u_host.wr;
    assign dbg_host_wa    = dut.u_chip.u_host.wa;
    assign dbg_host_wd    = dut.u_chip.u_host.wd;
    assign dbg_u0_level   = dut.u_chip.g_unit[0].u_unit.u_tx.lvl;
    assign dbg_u0_cursor_q = dut.u_chip.g_unit[0].u_unit.u_tx.eq;
    assign dbg_u0_cursor_r = dut.u_chip.g_unit[0].u_unit.u_tx.er;
    assign dbg_u0_due_level = dut.u_chip.g_unit[0].u_unit.u_tx.due_lvl_v;
    assign dbg_u0_pin_a    = dut.u_chip.g_unit[0].u_unit.pin_a;
    assign dbg_lane0_slots = {dut.u_chip.g_lane[0].u_lane.slots[53 +: 53],
                              dut.u_chip.g_lane[0].u_lane.slots[0 +: 53]};
endmodule

`default_nettype wire

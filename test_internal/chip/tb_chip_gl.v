// Gate-level L3 harness. Keep the same cocotb-visible pins as tb_chip.v, but
// instantiate the Tiny Tapeout top from a hardened netlist instead of trw_chip.
`default_nettype none
`timescale 1ns / 1ps

module tb_chip (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       ena,
    input  wire [7:0] ui_drv,
    input  wire       loop0,
    input  wire [7:0] uio_in,
    output wire [7:0] ui_in,
    output wire [7:0] uo_out,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe
);
    assign ui_in = {ui_drv[7:1], loop0 ? uo_out[0] : ui_drv[0]};

    tt_um_tripwire u_dut (
        .clk (clk), .rst_n (rst_n), .ena (ena), .ui_in (ui_in),
        .uo_out (uo_out), .uio_in (uio_in), .uio_out (uio_out), .uio_oe (uio_oe)
    );
endmodule

`default_nettype wire

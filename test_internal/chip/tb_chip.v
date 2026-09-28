// Chip-level harness (test_internal/chip): trw_chip with Tiny Tapeout's pins, the SRAM macro's behavioural
// model, and an optional loopback of uo0 into ui0 (for programs whose TX and RX pins are uo0 / ui0).
`default_nettype none
`timescale 1ns / 1ps

module tb_chip (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       ena,
    input  wire [7:0] ui_drv,          // what the test drives on ui_in
    input  wire       loop0,           // 1: ui_in[0] = uo_out[0]
    input  wire [7:0] uio_in,
    output wire [7:0] ui_in,
    output wire [7:0] uo_out,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe
);
    assign ui_in = {ui_drv[7:1], loop0 ? uo_out[0] : ui_drv[0]};

    trw_chip u_chip (
        .ui_in (ui_in), .uo_out (uo_out), .uio_in (uio_in), .uio_out (uio_out), .uio_oe (uio_oe),
        .ena (ena), .clk (clk), .rst_n (rst_n)
    );

    initial begin
        $dumpfile("tb_chip.fst");
        $dumpvars(0, tb_chip);
    end
endmodule

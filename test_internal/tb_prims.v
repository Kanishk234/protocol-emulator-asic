// Testbench wrapper for test_internal/test_prims.py: one timer and one shift register.
`default_nettype none
`timescale 1ns / 1ps

module tb_prims ();
    reg clk;
    reg t_rst, t_load, t_half, t_en;
    reg [16:0] t_cfg;
    wire t_tc;
    reg s_rst, s_load, s_step, s_sin;
    reg [7:0] s_d;
    reg [4:0] s_cfg;
    wire s_sout, s_done;
    wire [7:0] s_q;

    wp_timer u_timer (.CLK(clk), .rst(t_rst), .load(t_load), .half(t_half), .en(t_en),
                      .tc(t_tc), .ConfigBits(t_cfg));
    wp_shift u_shift (.CLK(clk), .rst(s_rst), .load(s_load), .step(s_step), .sin(s_sin),
                      .d(s_d), .sout(s_sout), .done(s_done), .q(s_q), .ConfigBits(s_cfg));
endmodule

// L1-CHAN harness (white-box, test_internal/): the generated fabric (trw_fabric.v, `TRW_NCONS consumer ports)
// with a trw_chan_prod register on every one of the `TRW_NPROD producers, so both halves are the real RTL. The
// test drives each producer's load request and token, each consumer's take, and the ports' configuration
// writes; it checks everything against a model of §14 F1-F7 every clock. The counts follow the spec
// (trw_defs.vh), so the harness also runs at other lane and unit counts.
`default_nettype none
`timescale 1ns / 1ps
`include "trw_defs.vh"

module tb_chan (
    input  wire                     clk,
    input  wire                     rst_n,
    input  wire [`TRW_NPROD-1:0]    load_req,
    input  wire [18*`TRW_NPROD-1:0] tok_in,
    input  wire [`TRW_NCONS-1:0]    take,
    input  wire [`TRW_NCONS-1:0]    cfg_we,
    input  wire                     cfg_en,
    input  wire                     cfg_tap,
    input  wire [3:0]               cfg_sel,
    input  wire [3:0]               cfg_accept,
    input  wire [`TRW_NCONS-1:0]    clr_dropped,
    output wire [`TRW_NPROD-1:0]    free,
    output wire [`TRW_NPROD-1:0]    load,
    output wire [`TRW_NPROD-1:0]    p_valid,
    output wire [`TRW_NPROD-1:0]    p_seq,
    output wire [18*`TRW_NPROD-1:0] p_tok,
    output wire [`TRW_NPROD-1:0]    all_taken,
    output wire [`TRW_NCONS-1:0]    avail,
    output wire [18*`TRW_NCONS-1:0] head,
    output wire [10*`TRW_NCONS-1:0] port_state,
    output wire [8*`TRW_NCONS-1:0]  dropped
);
    genvar p;
    generate
        for (p = 0; p < `TRW_NPROD; p = p + 1) begin : g_prod
            trw_chan_prod u_prod (
                .clk (clk), .rst_n (rst_n), .load_req (load_req[p]), .tok_in (tok_in[18*p +: 18]),
                .all_taken (all_taken[p]), .free (free[p]), .load (load[p]),
                .valid (p_valid[p]), .seq (p_seq[p]), .tok (p_tok[18*p +: 18])
            );
        end
    endgenerate

    trw_fabric u_fab (
        .clk (clk), .rst_n (rst_n),
        .p_valid (p_valid), .p_seq (p_seq), .p_load (load), .p_tok (p_tok), .all_taken (all_taken),
        .take (take), .avail (avail), .head (head),
        .cfg_we (cfg_we), .cfg_en (cfg_en), .cfg_tap (cfg_tap), .cfg_sel (cfg_sel), .cfg_accept (cfg_accept),
        .clr_dropped (clr_dropped), .port_state (port_state), .dropped (dropped)
    );

    initial begin
        $dumpfile("tb_chan.fst");
        $dumpvars(0, tb_chan);
    end
endmodule

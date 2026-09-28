// L1-HOST harness (white-box, test_internal/): trw_host behind the chip's input synchronisers, with
//   - the real owner registers (trw_pins) and a HOST_IN producer register (trw_chan_prod),
//   - a 512x16 SRAM model (registered read) on the host rotation slot (time mod 4 = 3),
//   - every other block's readback driven by the test (lane debug buses, ports, DROPPED, unit flags,
//     HOST_OUT head), and every write strobe visible to the test.
`default_nettype none
`timescale 1ns / 1ps
`include "trw_defs.vh"

module tb_host #(
    parameter NL = `TRW_LANES, parameter NU = `TRW_UNITS, parameter NC = `TRW_NCONS, parameter LDW = 180
) (
    input  wire              clk,
    input  wire              rst_n,
    input  wire              csn_pad,
    input  wire              sck_pad,
    input  wire              mosi_pad,
    output wire              miso,
    output wire              irq,
    output wire [NL-1:0]     run,
    output wire [NL-1:0]     step,
    output wire              live,
    output reg  [15:0]       tnow,
    output wire [NL-1:0]     slot_we,
    output wire [5:0]        slot_waddr,
    output wire [NL-1:0]     lane_hwe,
    output wire [2:0]        lane_hsel,
    output wire [15:0]       wdata,
    input  wire [NL*LDW-1:0] lane_dbg,
    output wire [NC-1:0]     port_we,
    output wire [NC-1:0]     clr_dropped,
    input  wire [10*NC-1:0]  port_state,
    input  wire [8*NC-1:0]   dropped,
    output wire [NU-1:0]     pcfg_we,
    output wire [4:0]        pcfg_waddr,
    output wire [NU-1:0]     clr_overrun,
    output wire [NU-1:0]     clr_late,
    input  wire [NU-1:0]     overrun,
    input  wire [NU-1:0]     late,
    output wire              hin_load,
    output wire              hin_valid,
    output wire [17:0]       hin_q,
    input  wire              hin_all_taken,
    input  wire              hout_avail,
    input  wire [17:0]       hout_head,
    output wire              hout_take,
    input  wire [8:0]        mem_haddr,
    output wire [15:0]       mem_hrd
);
    always @(posedge clk) begin
        if (!rst_n) tnow <= 16'd0;
        else        tnow <= tnow + 16'd1;
    end

    wire [2:0] s;
    trw_sync #(.W (3)) u_sync (.clk (clk), .d ({mosi_pad, sck_pad, csn_pad}), .q (s));

    wire        own_we;
    wire [3:0]  own_waddr, own_raddr;
    wire [2:0]  own_q;
    wire        hin_req, hin_free, hin_seq;
    wire [17:0] hin_tok;
    wire        mem_en, mem_we;
    wire [8:0]  mem_addr;
    wire [15:0] mem_wdata;
    reg  [15:0] rdata;

    trw_host #(.NL (NL), .NU (NU), .NC (NC), .LDW (LDW)) u_host (
        .clk (clk), .rst_n (rst_n), .csn (s[0]), .sck (s[1]), .mosi (s[2]), .miso (miso), .irq (irq),
        .run (run), .step (step), .live (live), .time_now (tnow),
        .slot_we (slot_we), .slot_waddr (slot_waddr), .lane_hwe (lane_hwe), .lane_hsel (lane_hsel),
        .wdata (wdata), .lane_dbg (lane_dbg),
        .port_we (port_we), .clr_dropped (clr_dropped), .port_state (port_state), .dropped (dropped),
        .pcfg_we (pcfg_we), .pcfg_waddr (pcfg_waddr), .clr_overrun (clr_overrun), .clr_late (clr_late),
        .overrun (overrun), .late (late),
        .own_we (own_we), .own_waddr (own_waddr), .own_raddr (own_raddr), .own_q (own_q),
        .hin_load_req (hin_req), .hin_tok (hin_tok), .hin_free (hin_free),
        .hout_avail (hout_avail), .hout_head (hout_head), .hout_take (hout_take),
        .host_slot (tnow[1:0] == 2'd3), .mem_en (mem_en), .mem_we (mem_we), .mem_addr (mem_addr),
        .mem_wdata (mem_wdata), .mem_rdata (rdata)
    );

    trw_pins #(.NU (NU)) u_pins (
        .clk (clk), .rst_n (rst_n), .own_we (own_we), .own_waddr (own_waddr), .own_wdata (wdata[2:0]),
        .own_raddr (own_raddr), .own_q (own_q),
        .a_out ({NU{1'b0}}), .a_oe ({NU{1'b0}}), .n_out ({NU{1'b0}}), .n_oe ({NU{1'b0}}),
        .pin_a ({NU{5'd31}}), .pin_n ({NU{5'd31}}), .pad_out (), .pad_oe ()
    );

    trw_chan_prod u_hin (
        .clk (clk), .rst_n (rst_n), .load_req (hin_req), .tok_in (hin_tok), .all_taken (hin_all_taken),
        .free (hin_free), .load (hin_load), .valid (hin_valid), .seq (hin_seq), .tok (hin_q)
    );

    reg [15:0] mem [0:511];
    always @(posedge clk)
        if (mem_en) begin
            if (mem_we) mem[mem_addr] <= mem_wdata;
            rdata <= mem[mem_addr];
        end
    assign mem_hrd = mem[mem_haddr];

    wire _unused = &{1'b0, hin_seq};
    initial begin
        $dumpfile("tb_host.fst");
        $dumpvars(0, tb_host);
    end
endmodule

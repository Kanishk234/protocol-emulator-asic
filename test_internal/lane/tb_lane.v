// L1 lane harness (white-box, test_internal/): one trw_lane as lane 0, with
//   - the slot and K contents driven directly by the test (flop-like; trw_slots.v is tested separately),
//   - the global time counter (0 at reset) and lane 0's rotation slot (time mod 4 == 0, §14 R1),
//   - a 512x16 SRAM model with a registered read, as the IHP macro (the test fills it while halted
//     through mem_h*, and can read any word combinationally),
//   - the input heads (I0, I1) and the output release terms driven by the test.
`default_nettype none
`timescale 1ns / 1ps
`include "trw_defs.vh"

module tb_lane (
    input  wire                         clk,
    input  wire                         rst_n,
    input  wire                         run,
    input  wire                         step,
    input  wire [12*`TRW_SLOT_BITS-1:0] slots,
    input  wire [63:0]                  k,
    input  wire [1:0]                   in_avail,
    input  wire [35:0]                  in_head,
    output wire [1:0]                   in_take,
    input  wire [1:0]                   out_all_taken,
    output wire [1:0]                   out_valid,
    output wire [1:0]                   out_seq,
    output wire [35:0]                  out_tok,
    output wire [1:0]                   out_load,
    input  wire                         host_we,
    input  wire [2:0]                   host_sel,
    input  wire [15:0]                  host_wdata,
    input  wire                         mem_hwe,
    input  wire [8:0]                   mem_haddr,
    input  wire [15:0]                  mem_hwd,
    output wire [15:0]                  mem_hrd,
    output reg  [15:0]                  tnow,
    output wire                         mem_en,
    output wire                         mem_we,
    output wire [8:0]                   mem_addr,
    output wire [63:0]                  dbg_regs,
    output wire [3:0]                   dbg_state,
    output wire [3:0]                   dbg_flags,
    output wire [2:0]                   dbg_pend,
    output wire [8:0]                   dbg_rpc,
    output wire                         dbg_rir_valid,
    output wire [15:0]                  dbg_rir,
    output wire                         dbg_rz
);
    always @(posedge clk) begin
        if (!rst_n) tnow <= 16'd0;
        else        tnow <= tnow + 16'd1;
    end

    reg  [15:0] mem [0:511];
    reg  [15:0] rdata;
    wire [15:0] mem_wdata;
    always @(posedge clk) begin
        if (mem_en) begin
            if (mem_we) mem[mem_addr] <= mem_wdata;
            rdata <= mem[mem_addr];
        end
        if (mem_hwe) mem[mem_haddr] <= mem_hwd;
    end
    assign mem_hrd = mem[mem_haddr];

    trw_lane u_lane (
        .clk (clk), .rst_n (rst_n), .run (run), .step (step), .slots (slots), .k (k), .time_now (tnow),
        .in_avail (in_avail), .in_head (in_head), .in_take (in_take),
        .out_all_taken (out_all_taken), .out_valid (out_valid), .out_seq (out_seq), .out_tok (out_tok),
        .out_load (out_load),
        .my_slot (tnow[1:0] == 2'd0), .mem_rdata (rdata), .mem_en (mem_en), .mem_we (mem_we),
        .mem_addr (mem_addr), .mem_wdata (mem_wdata),
        .host_we (host_we), .host_sel (host_sel), .host_wdata (host_wdata),
        .dbg_regs (dbg_regs), .dbg_state (dbg_state), .dbg_flags (dbg_flags), .dbg_pend (dbg_pend),
        .dbg_rpc (dbg_rpc), .dbg_rir_valid (dbg_rir_valid), .dbg_rir (dbg_rir), .dbg_rz (dbg_rz)
    );

    initial begin
        $dumpfile("tb_lane.fst");
        $dumpvars(0, tb_lane);
    end
endmodule

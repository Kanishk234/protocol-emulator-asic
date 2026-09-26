// R1 risk spike (throwaway): timing harness around one lane (L0).
//
// Everything the lane talks to is a register, so every path STA reports is register to register:
//   - 9 dummy producer registers (U0-U5.rx, HOST_IN, L1.O0, L2.O1) feeding two real consumer ports
//     with the D-029 legal-source lists (L0.I0: 8 sources, L0.I1: 9);
//   - dummy registered state for the subscribers of L0.O0 (8) and L0.O1 (9), from which the
//     producer release term all_taken is computed as in §4.4 / §14 F3;
//   - a dummy RIR (routine step), RUN bit and host write port for the slot store;
//   - the 16-bit global time counter.
// The dummy registers form one shift chain from `din`, so none of them is a constant. `dout` is an
// unconstrained XOR of the lane's outputs, only there to keep the logic alive through synthesis.
`default_nettype none
`include "trw_defs.vh"

module trw_r1_top (
    input  wire clk,
    input  wire rst_n,
    input  wire din,
    output wire dout
);
    localparam NP     = 9;
    localparam O_PROD = 0;                  // producers: {data16, tag2, seq, valid} x 9
    localparam O_CP   = O_PROD + 20*NP;     // consumer ports I0, I1: {accept4, sel4, en} x 2
    localparam O_SUB  = O_CP + 2*9;         // subscribers: {last_seq, sel4, blocking, en} x 17
    localparam O_RIR  = O_SUB + 17*7;       // {rir16, rir_valid}
    localparam O_HOST = O_RIR + 17;         // {wdata16, waddr6, we}
    localparam O_RUN  = O_HOST + 23;
    localparam CH     = O_RUN + 1;

    reg [CH-1:0] chain;
    always @(posedge clk) begin
        if (!rst_n)
            chain <= {CH{1'b0}};
        else
            chain <= {chain[CH-2:0], din};
    end

    reg [15:0] time_now;
    always @(posedge clk) begin
        if (!rst_n)
            time_now <= 16'd0;
        else
            time_now <= time_now + 16'd1;
    end

    // ---- dummy producers
    wire [NP-1:0]    p_valid, p_seq;
    wire [2*NP-1:0]  p_tag;
    wire [16*NP-1:0] p_data;
    genvar p;
    generate
        for (p = 0; p < NP; p = p + 1) begin : g_prod
            assign p_valid[p]         = chain[O_PROD + 20*p];
            assign p_seq[p]           = chain[O_PROD + 20*p + 1];
            assign p_tag[2*p +: 2]    = chain[O_PROD + 20*p + 2 +: 2];
            assign p_data[16*p +: 16] = chain[O_PROD + 20*p + 4 +: 16];
        end
    endgenerate

    // ---- consumer ports (legal sources, ARCHITECTURE.md §4.6)
    // L0.I0: U0-U5.rx, HOST_IN, L2.O1          L0.I1: U0-U5.rx, HOST_IN, L1.O0, L2.O1
    wire [1:0]  in_avail, in_take;
    wire [35:0] in_head;
    wire [1:0]  cp_last;

    trw_cport #(.N(8)) u_i0 (
        .clk (clk), .rst_n (rst_n),
        .en (chain[O_CP]), .sel (chain[O_CP+1 +: 4]), .accept (chain[O_CP+5 +: 4]),
        .src_valid ({p_valid[8], p_valid[6:0]}),
        .src_seq   ({p_seq[8],   p_seq[6:0]}),
        .src_tag   ({p_tag[17:16],   p_tag[13:0]}),
        .src_data  ({p_data[143:128], p_data[111:0]}),
        .take (in_take[0]), .avail (in_avail[0]), .head (in_head[17:0]), .last_seq (cp_last[0])
    );
    trw_cport #(.N(9)) u_i1 (
        .clk (clk), .rst_n (rst_n),
        .en (chain[O_CP+9]), .sel (chain[O_CP+10 +: 4]), .accept (chain[O_CP+14 +: 4]),
        .src_valid (p_valid), .src_seq (p_seq), .src_tag (p_tag), .src_data (p_data),
        .take (in_take[1]), .avail (in_avail[1]), .head (in_head[35:18]), .last_seq (cp_last[1])
    );

    // ---- subscribers of L0.O0 (8) and L0.O1 (9), and the release term (§4.4)
    // L0.O0 is sel 0 in U0-U5.tx and HOST_OUT, sel 7 in L2.I1.
    // L0.O1 is sel 3 in U0-U5.tx and HOST_OUT, sel 7 in L1.I0, sel 8 in L2.I1.
    wire [1:0] out_valid, out_seq;
    wire [16:0] sub_done;
    genvar q;
    generate
        for (q = 0; q < 17; q = q + 1) begin : g_sub
            localparam [3:0] CODE = (q < 7) ? 4'd0 : (q == 7) ? 4'd7 : (q < 15) ? 4'd3
                                  : (q == 15) ? 4'd7 : 4'd8;
            localparam PORT = (q < 8) ? 0 : 1;
            wire       en   = chain[O_SUB + 7*q];
            wire       blk  = chain[O_SUB + 7*q + 1];
            wire [3:0] sel  = chain[O_SUB + 7*q + 2 +: 4];
            wire       last = chain[O_SUB + 7*q + 6];
            assign sub_done[q] = !(en && blk && (sel == CODE)) || (last == out_seq[PORT]);
        end
    endgenerate
    wire [1:0] out_all_taken = {&sub_done[16:8], &sub_done[7:0]};

    // ---- slot store and lane
    wire [12*`TRW_SLOT_BITS-1:0] slots;
    wire [15:0] slot_rd;
    wire [63:0] k;
    trw_slots u_slots (
        .clk (clk), .rst_n (rst_n),
        .we (chain[O_HOST]), .waddr (chain[O_HOST+1 +: 6]), .wdata (chain[O_HOST+7 +: 16]),
        .slots (slots), .k (k), .raddr (6'd0), .rdata (slot_rd)   // debug read unused here
    );

    wire [35:0] out_tok;
    wire        rt_take, rt_nz, rz, call_req, rb;
    wire [4:0]  call_idx;
    wire [74:0] lane_dbg;
    trw_lane u_lane (
        .clk (clk), .rst_n (rst_n), .run (chain[O_RUN]),
        .slots (slots), .k (k), .time_now (time_now),
        .in_avail (in_avail), .in_head (in_head), .in_take (in_take),
        .out_all_taken (out_all_taken), .out_valid (out_valid), .out_seq (out_seq), .out_tok (out_tok),
        .rir_valid (chain[O_RIR]), .rir (chain[O_RIR+1 +: 16]),
        .rt_take (rt_take), .rt_nz (rt_nz), .rz (rz),
        .call_req (call_req), .call_idx (call_idx), .rb_o (rb), .dbg (lane_dbg)
    );

    assign dout = ^{out_tok, out_valid, out_seq, in_take, cp_last, rt_take, rt_nz, rz,
                    call_req, call_idx, rb, chain[CH-1], slot_rd, lane_dbg};
endmodule

// One lane's slot store: 12 reflex slots (53 bits, ISA.md §4.1) and K0-K3, as a latch array (D-034),
// write-only from the host (D-039). From the R1 spike (spikes/r1_lane/trw_slots.v); the debug read port
// is gone (D-039), and slot word 3 stores only its 5 used bits.
//
// Host words (16 bits each) are the write unit (§9: `slot[7:4] word[1:0]`, slot index 12 = K, §14 H1):
//   waddr 0..47   slot waddr[5:2], word waddr[1:0]: w0 = bits [15:0], w1 = [31:16], w2 = [47:32],
//                 w3[4:0] = [52:48] (the other bits of w3 are not stored)
//   waddr 48..51  K0..K3; waddr 52..63 are ignored
//
// Timing contract:
//   - Clock n: `we`, `waddr`, `wdata` from the host. The write data is registered at edge n. Each word
//     has its own library clock gate (sg13cmos5l_lgcp_1: GATE latched while clk is low, ANDed with clk),
//     so the word's latches are transparent during the high phase of clock n+1 while the registered data
//     is stable, and `slots`/`k` show the new value from the middle of clock n+1.
//   - Written only while the lane is halted (§9), so the outputs are static while it runs: paths from
//     them are false paths in the latch SDC exception (D-032).
//   - The latches have no reset: the host writes all 52 words before RUN (§14 H1).
// TRW_SLOTS_FLOPS: a flop version with the same interface and timing (FPGA build, fallback).
`default_nettype none
`include "trw_defs.vh"

module trw_slots (
    input  wire                         clk,
    input  wire                         rst_n,
    input  wire                         we,
    input  wire [5:0]                   waddr,
    input  wire [15:0]                  wdata,
    output wire [12*`TRW_SLOT_BITS-1:0] slots,
    output wire [63:0]                  k        // {K3, K2, K1, K0}
);
    localparam NWORDS = 52;

    wire [16*NWORDS-1:0] words;

`ifndef TRW_SLOTS_FLOPS
    reg [15:0] wdata_q;
    always @(posedge clk) begin
        if (!rst_n)
            wdata_q <= 16'h0000;
        else
            wdata_q <= wdata;
    end
`endif

    genvar w;
    generate
        for (w = 0; w < NWORDS; w = w + 1) begin : g_word
            // bits stored: 5 for word 3 of a slot, 16 otherwise
            localparam NB = ((w < 48) && (w % 4 == 3)) ? 5 : 16;
            wire dec = we && (waddr == w);
            reg [NB-1:0] mem;
`ifdef TRW_SLOTS_FLOPS
            always @(posedge clk) begin
                if (!rst_n)
                    mem <= {NB{1'b0}};
                else if (dec)
                    mem <= wdata[NB-1:0];
            end
`else
            wire gclk;
            /* verilator lint_off LATCH */
`ifdef SYNTHESIS
            // Synthesis (Yosys, LibreLane): the library's integrated clock gate.
            sg13cmos5l_lgcp_1 u_icg (.GCLK (gclk), .CLK (clk), .GATE (dec));
`else
            // Simulation and lint: the same function, an enable latch transparent while clk is low,
            // ANDed with clk (intentional latch).
            reg en_l;
            always @* begin
                if (!clk)
                    en_l = dec;
            end
            assign gclk = clk & en_l;
`endif
            // Word latch, transparent while the gated clock is high (intentional latch).
            always @* begin
                if (gclk)
                    mem = wdata_q[NB-1:0];
            end
            /* verilator lint_on LATCH */
`endif
            if (NB == 16) begin : g_full
                assign words[16*w +: 16] = mem;
            end else begin : g_part
                assign words[16*w +: 16] = {{(16-NB){1'b0}}, mem};
            end
        end
    endgenerate

    genvar s;
    generate
        for (s = 0; s < 12; s = s + 1) begin : g_slot
            assign slots[s*`TRW_SLOT_BITS +: `TRW_SLOT_BITS] = words[64*s +: `TRW_SLOT_BITS];
        end
    endgenerate
    assign k = words[16*48 +: 64];

    // Host word 3 of each slot: bits [15:5] are constant 0 (not stored).
    wire _unused = &{1'b0, words[64*0+53 +: 11], words[64*1+53 +: 11], words[64*2+53 +: 11],
                     words[64*3+53 +: 11], words[64*4+53 +: 11], words[64*5+53 +: 11],
                     words[64*6+53 +: 11], words[64*7+53 +: 11], words[64*8+53 +: 11],
                     words[64*9+53 +: 11], words[64*10+53 +: 11], words[64*11+53 +: 11]};
endmodule

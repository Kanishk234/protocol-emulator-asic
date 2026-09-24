// R1 risk spike (throwaway): one lane's slot store, 12 reflex slots + K0-K3.
//
// Host words (16 bits each) are the write unit:
//   waddr 0..47  slot waddr[5:2], host word waddr[1:0] (ISA.md §4.1: w0 = bits [15:0] ... w3[4:0] = [52:48])
//   waddr 48..51 K0..K3
//
// ASIC build: a latch array, Ibex style (PHYSICAL_DESIGN_AND_CI.md §4). The write data is registered;
// each word has its own clock gate (a latch transparent while clk is low, ANDed with clk), so a word's
// latches are transparent during the high phase of the clock after the write request, while the
// registered data is stable. Written only while the lane is halted.
// TRW_SLOTS_FLOPS: the flop fallback (and the FPGA build), same interface and timing.
//
// Latches have no reset: the host must write every slot word (at least V = 0) before RUN.
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

`ifdef TRW_SLOTS_FLOPS
    genvar w;
    generate
        for (w = 0; w < NWORDS; w = w + 1) begin : g_word
            reg [15:0] mem;
            always @(posedge clk) begin
                if (!rst_n)
                    mem <= 16'h0000;
                else if (we && (waddr == w))
                    mem <= wdata;
            end
            assign words[16*w +: 16] = mem;
        end
    endgenerate
`else
    reg [15:0] wdata_q;
    always @(posedge clk) begin
        if (!rst_n)
            wdata_q <= 16'h0000;
        else
            wdata_q <= wdata;
    end

    genvar w;
    generate
        for (w = 0; w < NWORDS; w = w + 1) begin : g_word
            wire dec = we && (waddr == w);
            reg  en_l;
            reg  [15:0] mem;
            /* verilator lint_off LATCH */
            // Clock gate: enable latch, transparent while clk is low (intentional latch).
            always @* begin
                if (!clk)
                    en_l = dec;
            end
            wire gclk = clk & en_l;
            // Word latch, transparent while the gated clock is high (intentional latch).
            always @* begin
                if (gclk)
                    mem = wdata_q;
            end
            /* verilator lint_on LATCH */
            assign words[16*w +: 16] = mem;
        end
    endgenerate
`endif

    genvar s;
    generate
        for (s = 0; s < 12; s = s + 1) begin : g_slot
            assign slots[s*`TRW_SLOT_BITS +: `TRW_SLOT_BITS] = words[64*s +: `TRW_SLOT_BITS];
        end
    endgenerate
    assign k = words[16*48 +: 64];

    // Host word 3 of each slot only uses bits [4:0].
    wire _unused = &{1'b0, words[64*0+53 +: 11], words[64*1+53 +: 11], words[64*2+53 +: 11],
                     words[64*3+53 +: 11], words[64*4+53 +: 11], words[64*5+53 +: 11],
                     words[64*6+53 +: 11], words[64*7+53 +: 11], words[64*8+53 +: 11],
                     words[64*9+53 +: 11], words[64*10+53 +: 11], words[64*11+53 +: 11]};
endmodule

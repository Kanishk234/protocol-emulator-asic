// Pin-unit configuration block: one unit's ARCHITECTURE.md §7.2 registers (D-036), as a latch array
// (D-038), write-only from the host (D-039). Field positions come from src/trw_defs.vh, which is
// generated from spec/tripwire.yaml (`TRW_PC_*`).
//
// FULL = 1 stores every field (U0-U1); FULL = 0 stores only the core fields (U2-U5, D-040): writes to
// the PULSE, carrier and BITSYNC fields are ignored and those bits read 0. Bits that no field uses are
// never stored and read 0.
//
// Timing contract:
//   - Clock n: `we`, `waddr` (word 0..31 inside the unit's block) and `wdata` come from the host.
//     Words >= TRW_PC_WORDS are ignored.
//   - The write data is registered at edge n. Each word that stores any bit has its own library clock
//     gate (sg13cmos5l_lgcp_1: GATE latched while clk is low, ANDed with clk), so the word's latches
//     are transparent during the high phase of clock n+1, while the registered data is stable, and
//     `cfg` shows the new value from the middle of clock n+1 (the pattern of trw_slots.v, R2).
//   - `restart` is 1 in clock n+1 for any write to the block (the unit restarts at edge n+1).
//   - Written only while the lanes are halted (§14 H1), so `cfg` is static while running: paths from
//     it are false paths in the latch SDC exception (D-032).
//   - The latches have no reset: until the host writes a word, its bits are undefined (§14 H1).
// TRW_PIN_CFG_FLOPS: a flop version with the same interface and timing (FPGA build, fallback).
`default_nettype none
`include "trw_defs.vh"

module trw_pin_cfg #(
    parameter FULL = 1
) (
    input  wire                    clk,
    input  wire                    rst_n,
    input  wire                    we,
    input  wire [4:0]              waddr,
    input  wire [15:0]             wdata,
    output wire [`TRW_PC_BITS-1:0] cfg,
    output reg                     restart
);
    localparam NW = `TRW_PC_WORDS;
    localparam [`TRW_PC_BITS-1:0] OPT = `TRW_PC_MASK_PULSE | `TRW_PC_MASK_CARRIER | `TRW_PC_MASK_BITSYNC;
    localparam [`TRW_PC_BITS-1:0] STORE = `TRW_PC_MASK_CORE | (FULL ? OPT : {`TRW_PC_BITS{1'b0}});

    always @(posedge clk) begin
        if (!rst_n)
            restart <= 1'b0;
        else
            restart <= we && (waddr < NW);
    end

    reg [15:0] wdata_q;
    always @(posedge clk) begin
        if (!rst_n)
            wdata_q <= 16'h0000;
        else
            wdata_q <= wdata;
    end

    genvar w, b;
    generate
        for (w = 0; w < NW; w = w + 1) begin : g_word
            if (|STORE[16*w +: 16]) begin : g_stored
                wire dec = we && (waddr == w);
`ifdef TRW_PIN_CFG_FLOPS
                reg [15:0] mem;
                always @(posedge clk) begin
                    if (!rst_n)
                        mem <= 16'h0000;
                    else if (dec)
                        mem <= wdata;
                end
                for (b = 0; b < 16; b = b + 1) begin : g_bit
                    assign cfg[16*w + b] = STORE[16*w + b] ? mem[b] : 1'b0;
                end
`else
                wire gclk;
                /* verilator lint_off LATCH */
`ifdef SYNTHESIS
                // Synthesis (Yosys, LibreLane): the library's integrated clock gate.
                sg13cmos5l_lgcp_1 u_icg (.GCLK (gclk), .CLK (clk), .GATE (dec));
`else
                // Simulation and lint: the same function, an enable latch transparent while clk is
                // low, ANDed with clk (intentional latch).
                reg en_l;
                always @* begin
                    if (!clk)
                        en_l = dec;
                end
                assign gclk = clk & en_l;
`endif
                for (b = 0; b < 16; b = b + 1) begin : g_bit
                    if (STORE[16*w + b]) begin : g_latch
                        // Transparent while the gated clock is high (intentional latch).
                        reg q;
                        always @* begin
                            if (gclk)
                                q = wdata_q[b];
                        end
                        assign cfg[16*w + b] = q;
                    end else begin : g_none
                        assign cfg[16*w + b] = 1'b0;
                    end
                end
                /* verilator lint_on LATCH */
`endif
            end else begin : g_empty
                assign cfg[16*w +: 16] = 16'h0000;
            end
        end
    endgenerate

`ifdef TRW_PIN_CFG_FLOPS
    wire _unused = &{1'b0, wdata_q};
`endif
endmodule

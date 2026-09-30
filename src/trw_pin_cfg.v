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
//   - Writes are legal while lanes are halted, including after activation. Pin units remain live, so
//     configuration-to-state paths stay timed (D-066); the latch SDC exception does not cut them.
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
    output wire                    carrier_active,
    output reg                     restart
);
    localparam NW = `TRW_PC_WORDS;
    localparam [`TRW_PC_BITS-1:0] OPT = `TRW_PC_MASK_PULSE | `TRW_PC_MASK_CARRIER | `TRW_PC_MASK_BITSYNC;
    localparam [`TRW_PC_BITS-1:0] STORE = `TRW_PC_MASK_CORE | ((FULL != 0) ? OPT : {`TRW_PC_BITS{1'b0}});
    localparam integer CARRIER_WORD0 = `TRW_PC_CARRIER_LSB / 16;
    localparam integer CARRIER_WORD1 = `TRW_PC_CARRIER_MSB / 16;

    // Cache P-G25's carrier-enabled predicate beside the configuration latches. The high nine
    // carrier fraction bits are ignored when deciding whether the period reaches two clocks.
    // Carrier bits [15:9] are in word 13 bits [15:9]; bits [23:16] are in word 14 bits [7:0].
    generate
        if (FULL != 0) begin : g_carrier_active
            wire carrier_write = (we && ((waddr == CARRIER_WORD0[4:0]) || (waddr == CARRIER_WORD1[4:0])));
`ifndef TRW_PIN_CFG_FLOPS
            wire carrier_active_next = (waddr == CARRIER_WORD0[4:0])
                                     ? ((|wdata_q[15:9]) | (|cfg[`TRW_PC_CARRIER_MSB:`TRW_PC_CARRIER_LSB+16]))
                                     : ((|cfg[`TRW_PC_CARRIER_LSB+15:`TRW_PC_CARRIER_LSB+9]) | (|wdata_q[7:0]));
`endif
`ifdef TRW_PIN_CFG_FLOPS
            reg active_q;
            always @(posedge clk) begin
                if (!rst_n)
                    active_q <= 1'b0;
                else if (carrier_write)
                    active_q <= (waddr == CARRIER_WORD0[4:0])
                              ? ((|wdata[15:9]) | (|cfg[`TRW_PC_CARRIER_MSB:`TRW_PC_CARRIER_LSB+16]))
                              : ((|cfg[`TRW_PC_CARRIER_LSB+15:`TRW_PC_CARRIER_LSB+9]) | (|wdata[7:0]));
            end
            assign carrier_active = active_q;
`else
            wire active_gclk;
`ifdef SYNTHESIS
            sg13cmos5l_lgcp_1 u_icg_active (
                .GCLK (active_gclk), .CLK (clk), .GATE (carrier_write)
            );
`else
            reg active_en_l;
            /* verilator lint_off LATCH */
            always @* begin
                if (!clk)
                    active_en_l = carrier_write;
            end
            /* verilator lint_on LATCH */
            assign active_gclk = clk & active_en_l;
`endif
            reg active_q;
            /* verilator lint_off LATCH */
            always @* begin
                if (active_gclk)
                    active_q = carrier_active_next;
            end
            /* verilator lint_on LATCH */
            assign carrier_active = active_q;
`endif
        end else begin : g_no_carrier_active
            assign carrier_active = 1'b0;
        end
    endgenerate

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

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
    output wire                    carrier_active, bitsync_active,
    output wire [24:0]             sample_delta,
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
                                     ? ((|(((CARRIER_WORD0 % 2) != 0) ? wdata_odd[15:9] : wdata_even[15:9])) | (|cfg[`TRW_PC_CARRIER_MSB:`TRW_PC_CARRIER_LSB+16]))
                                     : ((|cfg[`TRW_PC_CARRIER_LSB+15:`TRW_PC_CARRIER_LSB+9]) | (|(((CARRIER_WORD1 % 2) != 0) ? wdata_odd[7:0] : wdata_even[7:0])));
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

    // Configuration-only arithmetic; same high-phase visibility as its inputs.
    wire [24:0] sample_delta_value = {1'b0, cfg[`TRW_PC_SAMPLEOFS_MSB:`TRW_PC_SAMPLEOFS_LSB]}
                                   - {1'b0, cfg[`TRW_PC_PERIOD_MSB:`TRW_PC_PERIOD_LSB]};
`ifdef TRW_PIN_CFG_FLOPS
    assign sample_delta = sample_delta_value;
`else
    generate if (FULL != 0) begin: g_sample_delta
        wire delta_write = we && (waddr >= (`TRW_PC_PERIOD_LSB / 16))
                              && (waddr <= (`TRW_PC_SAMPLEOFS_MSB / 16));
        wire [15:0] delta_data = rst_n ? wdata : 16'd0;
        wire [23:0] next_period = (waddr == (`TRW_PC_PERIOD_LSB / 16))
                               ? {cfg[`TRW_PC_PERIOD_MSB:`TRW_PC_PERIOD_LSB+16], delta_data}
                               : (waddr == (`TRW_PC_PERIOD_MSB / 16))
                               ? {delta_data[7:0], cfg[`TRW_PC_PERIOD_LSB+15:`TRW_PC_PERIOD_LSB]}
                               : cfg[`TRW_PC_PERIOD_MSB:`TRW_PC_PERIOD_LSB];
        wire [23:0] next_sample = (waddr == (`TRW_PC_SAMPLEOFS_LSB / 16))
                               ? {cfg[`TRW_PC_SAMPLEOFS_MSB:`TRW_PC_SAMPLEOFS_LSB+16], delta_data}
                               : (waddr == (`TRW_PC_SAMPLEOFS_MSB / 16))
                               ? {delta_data[7:0], cfg[`TRW_PC_SAMPLEOFS_LSB+15:`TRW_PC_SAMPLEOFS_LSB]}
                               : cfg[`TRW_PC_SAMPLEOFS_MSB:`TRW_PC_SAMPLEOFS_LSB];
        wire [8:0] next_delta = {1'b0, next_sample[7:0]} - {1'b0, next_period[7:0]};
        reg [8:0] delta_stage;
        always @(posedge clk) begin
            if (!rst_n)
                delta_stage <= delta_write ? next_delta : 9'd0;
            else if (delta_write)
                delta_stage <= next_delta;
        end
        wire delta_gclk;
`ifdef SYNTHESIS
        sg13cmos5l_lgcp_1 u_icg_delta (.GCLK(delta_gclk), .CLK(clk), .GATE(delta_write));
`else
        reg delta_en_l;
        /* verilator lint_off LATCH */
        always @* begin
            if (!clk) delta_en_l = delta_write;
        end
        /* verilator lint_on LATCH */
        assign delta_gclk = clk & delta_en_l;
`endif
        reg [8:0] delta_q;
        /* verilator lint_off LATCH */
        always @* begin
            if (delta_gclk) delta_q = delta_stage;
        end
        /* verilator lint_on LATCH */
        wire [17:0] upper_sub = {1'b0, cfg[`TRW_PC_SAMPLEOFS_MSB:`TRW_PC_SAMPLEOFS_LSB+8], 1'b0}
                                          - {1'b0, cfg[`TRW_PC_PERIOD_MSB:`TRW_PC_PERIOD_LSB+8], delta_q[8]};
        assign sample_delta = {upper_sub[17:1], delta_q[7:0]};
    end else begin: g_no_sample_delta
        assign sample_delta = sample_delta_value;
    end endgenerate
`endif

    always @(posedge clk) begin
        if (!rst_n)
            restart <= 1'b0;
        else
            restart <= we && (waddr < NW);
    end

    // Two independently enabled word-parity banks reduce the physical spread and
    // load of each staged write-data bit without changing a word's write edge.
    reg [15:0] wdata_even, wdata_odd;
    always @(posedge clk) begin
        if (!rst_n) begin
            wdata_even <= 16'h0000;
            wdata_odd <= 16'h0000;
        end else if (we) begin
            if (waddr[0]) wdata_odd <= wdata;
            else wdata_even <= wdata;
        end
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
                        if ((16*w + b) == `TRW_PC_IDLE_LSB) begin : g_timing_ff
                            // Same write edge/visibility as the staged latch. Reset
                            // clears this stored bit only when its word is written.
                            always @(posedge clk) begin
                                if (dec) q <= rst_n ? wdata[b] : 1'b0;
                            end
                        end else begin : g_latched
                            always @* begin
                                if (gclk)
                                    q = ((w % 2) != 0) ? wdata_odd[b] : wdata_even[b];
                            end
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

    // Decode the joint mode at configuration time, with the same visibility as word 0.
    // This removes a late five-bit decode from the combinational pad-feedback path.
    generate if (FULL != 0) begin : g_bitsync_active
        wire mode_write = we && (waddr == 5'd0);
        wire mode_value = (wdata[`TRW_PC_TXMODE_MSB:`TRW_PC_TXMODE_LSB] == `TRW_PCE_TXMODE_BITSYNC)
                       && (wdata[`TRW_PC_RXMODE_MSB:`TRW_PC_RXMODE_LSB] == `TRW_PCE_RXMODE_BITSYNC);
`ifdef TRW_PIN_CFG_FLOPS
        reg mode_q;
        always @(posedge clk) begin
            if (!rst_n) mode_q <= 1'b0;
            else if (mode_write) mode_q <= mode_value;
        end
`else
        reg mode_stage;
        always @(posedge clk) begin
            if (!rst_n) mode_stage <= 1'b0;
            else if (mode_write) mode_stage <= mode_value;
        end
        wire mode_gclk;
`ifdef SYNTHESIS
        sg13cmos5l_lgcp_1 u_icg_mode (.GCLK(mode_gclk), .CLK(clk), .GATE(mode_write));
`else
        reg mode_en_l;
        /* verilator lint_off LATCH */
        always @* begin
            if (!clk) mode_en_l = mode_write;
        end
        /* verilator lint_on LATCH */
        assign mode_gclk = clk & mode_en_l;
`endif
        reg mode_q;
        /* verilator lint_off LATCH */
        always @* begin
            if (mode_gclk) mode_q = mode_stage;
        end
        /* verilator lint_on LATCH */
`endif
        assign bitsync_active = mode_q;
    end else begin : g_no_bitsync_active
        assign bitsync_active = 1'b0;
    end endgenerate

`ifdef TRW_PIN_CFG_FLOPS
    wire _unused = &{1'b0, wdata_even, wdata_odd};
`endif
endmodule

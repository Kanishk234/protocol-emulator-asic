// The shared operation table (ISA.md §3): one ALU per lane, used by the reflex slots and the routine steps.
// From the R1 spike (spikes/r1_lane/trw_alu.v, D-030), unchanged in function.
//
// Timing contract: purely combinational. The caller selects the operands (A, B, F, r[F[5:4]] for SHOR, and
// CMPM's M and V from K or r) and applies the results: d to the destination, R to f[DF] (reflex, DFE) or RZ
// (routine). MKCTL's CTRL tag and CALL's routine start are the lane's; here CALL gives d = 0, R = 0.
`default_nettype none
`include "trw_defs.vh"

module trw_alu (
    input  wire [3:0]  op,
    input  wire [15:0] a,
    input  wire [15:0] b,
    input  wire [7:0]  f,     // field operand F
    input  wire [15:0] rf,    // r[F[5:4]], for SHOR
    input  wire [15:0] m,     // CMPM mask
    input  wire [15:0] v,     // CMPM value
    output reg  [15:0] d,     // data result
    output reg         r      // flag result R
);
    // One left and one right shifter, shared by SHL/SHR (amount B[3:0]) and SHOR/EXT (amount F[3:0]).
    wire        use_f = (op == `TRW_OP_SHOR) || (op == `TRW_OP_EXT);
    wire [3:0]  sh    = use_f ? f[3:0] : b[3:0];
    wire [15:0] shl   = a << sh;
    wire [15:0] shr   = a >> sh;
    wire [15:0] emask = 16'hFFFF >> (4'd15 - f[7:4]);   // mask(F[7:4] + 1)

    always @* begin
        case (op)
            `TRW_OP_MOV:   d = a;
            `TRW_OP_ADD:   d = a + b;
            `TRW_OP_SUB:   d = a - b;
            `TRW_OP_AND:   d = a & b;
            `TRW_OP_OR:    d = a | b;
            `TRW_OP_XOR:   d = a ^ b;
            `TRW_OP_SHL:   d = shl;
            `TRW_OP_SHR:   d = shr;
            `TRW_OP_SHOR:  d = shl | rf;
            `TRW_OP_EXT:   d = shr & emask;
            `TRW_OP_MKCTL: d = {f[7:4], a[11:0]};
            `TRW_OP_CALL:  d = 16'h0000;
            `TRW_OP_MOVB:  d = b;
            default:       d = a;    // CMPM, LTU, PAR pass A through
        endcase
    end

    always @* begin
        case (op)
            `TRW_OP_CMPM: r = ((a & m) == v);
            `TRW_OP_LTU:  r = (a < b);
            `TRW_OP_PAR:  r = ^a;
            `TRW_OP_CALL: r = 1'b0;
            default:      r = (d == 16'h0000);
        endcase
    end
endmodule

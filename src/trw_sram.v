// R3 risk spike: the routine/data store behind the interface PHYSICAL_DESIGN_AND_CI.md §3 fixes
// for both the macro and its fallback: one access per clock, rdata one clock after a read.
//
//   en && !we  read addr; rdata holds SRAM[addr] from the next clock until the next read
//   en &&  we  write wdata to addr (all 16 bits); no read, rdata holds
//   !en        no access; rdata holds
//
// Macro pins (RM_IHPSG13_1P_512x16_c2_bm_bist, from the vendored model; all enables active high):
//   A_MEN = en (and 0 in reset), A_WEN = we, A_REN = !we: with both WEN and REN high the macro
//   writes through and returns the written data, not a read. A_DLY must be 1 (the model stops
//   otherwise). A_BM all ones (no partial writes). BIST port off and tied to 0.
// The instance name `sram` is part of the flattened path in src/config.json (MACROS,
// PDN_MACRO_CONNECTIONS): u_sram.sram. Rename both together.
`default_nettype none

module trw_sram (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        en,
    input  wire        we,
    input  wire [8:0]  addr,
    input  wire [15:0] wdata,
    output wire [15:0] rdata
);
    wire men = en && rst_n;

    RM_IHPSG13_1P_512x16_c2_bm_bist sram (
        .A_CLK       (clk),
        .A_MEN       (men),
        .A_WEN       (we),
        .A_REN       (!we),
        .A_ADDR      (addr),
        .A_DIN       (wdata),
        .A_DLY       (1'b1),
        .A_DOUT      (rdata),
        .A_BM        (16'hFFFF),
        .A_BIST_CLK  (1'b0),
        .A_BIST_EN   (1'b0),
        .A_BIST_MEN  (1'b0),
        .A_BIST_WEN  (1'b0),
        .A_BIST_REN  (1'b0),
        .A_BIST_ADDR (9'd0),
        .A_BIST_DIN  (16'd0),
        .A_BIST_BM   (16'd0)
    );
endmodule
